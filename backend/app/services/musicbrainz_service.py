import time
import json
import hashlib
import threading
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import ApiCache
from backend.app.logging_config import record_log

MUSICBRAINZ_BASE_URL = "https://musicbrainz.org/ws/2"

class MusicBrainzRateLimiter:
    """Thread-safe rate limiter strictly enforcing MusicBrainz 1 req/sec policy."""
    def __init__(self, min_interval: float = 1.05):
        self.min_interval = min_interval
        self.last_call = 0.0
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_call = time.time()

mb_limiter = MusicBrainzRateLimiter()

class MusicBrainzService:
    @staticmethod
    def _params_hash(params: Dict[str, Any]) -> str:
        s = json.dumps(params, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_response(cls, db: Session, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        p_hash = cls._params_hash(params)
        now = datetime.now(timezone.utc)
        cached = (
            db.query(ApiCache)
            .filter(
                ApiCache.source == "musicbrainz",
                ApiCache.endpoint == endpoint,
                ApiCache.params_hash == p_hash
            )
            .first()
        )
        if cached:
            if cached.expires_at > now:
                return json.loads(cached.payload_json)
            else:
                # Mark stale if expired
                cached.is_stale = True
                db.commit()
                # Return stale data if needed as fallback, but indicate provenance
        return None

    @classmethod
    def save_cache_response(
        cls, db: Session, endpoint: str, params: Dict[str, Any], status: int, data: Dict[str, Any], ttl_hours: int = 12
    ):
        p_hash = cls._params_hash(params)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)
        cached = (
            db.query(ApiCache)
            .filter(
                ApiCache.source == "musicbrainz",
                ApiCache.endpoint == endpoint,
                ApiCache.params_hash == p_hash
            )
            .first()
        )
        payload_str = json.dumps(data)
        if cached:
            cached.payload_json = payload_str
            cached.response_status = status
            cached.fetched_at = now
            cached.expires_at = expires
            cached.is_stale = False
        else:
            cached = ApiCache(
                source="musicbrainz",
                endpoint=endpoint,
                params_hash=p_hash,
                response_status=status,
                payload_json=payload_str,
                fetched_at=now,
                expires_at=expires,
                is_stale=False
            )
            db.add(cached)
        db.commit()

    @classmethod
    def request(cls, db: Session, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Queries MusicBrainz with rate limit, caching, timeouts, retries and backoff."""
        cached_data = cls.get_cached_response(db, endpoint, params)
        if cached_data:
            return cached_data

        url = f"{MUSICBRAINZ_BASE_URL}/{endpoint}"
        query_params = {**params, "fmt": "json"}
        headers = {
            "User-Agent": settings.MUSICBRAINZ_USER_AGENT,
            "Accept": "application/json",
        }

        max_retries = 3
        backoff = 1.5
        last_error = None

        for attempt in range(max_retries):
            mb_limiter.acquire()
            start_t = time.time()
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, params=query_params, headers=headers)
                    duration_ms = (time.time() - start_t) * 1000

                    if resp.status_code == 200:
                        data = resp.json()
                        cls.save_cache_response(db, endpoint, params, 200, data, ttl_hours=24)
                        record_log("INFO", f"MusicBrainz {endpoint} fetch successful", details={"duration_ms": duration_ms, "params": params})
                        return data
                    elif resp.status_code == 503 or resp.status_code == 429:
                        record_log("WARNING", f"MusicBrainz rate limited (HTTP {resp.status_code}), retry {attempt + 1}", details={"params": params})
                        time.sleep(backoff * (attempt + 1))
                        continue
                    else:
                        record_log("ERROR", f"MusicBrainz HTTP {resp.status_code}", details={"body": resp.text[:200]})
                        last_error = f"HTTP {resp.status_code}"
                        break
            except Exception as e:
                record_log("ERROR", f"MusicBrainz connection exception: {str(e)}", details={"attempt": attempt + 1})
                last_error = str(e)
                time.sleep(backoff * (attempt + 1))

        # Check for stale cache as fallback
        p_hash = cls._params_hash(params)
        stale = (
            db.query(ApiCache)
            .filter(
                ApiCache.source == "musicbrainz",
                ApiCache.endpoint == endpoint,
                ApiCache.params_hash == p_hash
            )
            .first()
        )
        if stale:
            record_log("WARNING", f"MusicBrainz using stale cache due to failure: {last_error}")
            data = json.loads(stale.payload_json)
            data["_stale_cached"] = True
            data["_fetched_at"] = stale.fetched_at.isoformat()
            return data

        return {"error": f"MusicBrainz request failed: {last_error}", "recordings": [], "releases": []}

    @classmethod
    def search_recordings(cls, db: Session, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        endpoint = "recording"
        params = {"query": query, "limit": limit}
        res = cls.request(db, endpoint, params)
        return res.get("recordings", [])

    @classmethod
    def get_new_releases(cls, db: Session, limit: int = 15) -> List[Dict[str, Any]]:
        """Queries genuine recent releases from MusicBrainz."""
        endpoint = "release"
        # Search releases from recent years with official status
        params = {"query": "date:[2023-01-01 TO 2026-12-31] AND status:official AND type:album", "limit": limit}
        res = cls.request(db, endpoint, params)
        return res.get("releases", [])
