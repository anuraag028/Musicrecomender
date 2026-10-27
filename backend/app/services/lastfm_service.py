import json
import hashlib
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import ApiCache
from backend.app.logging_config import record_log

LASTFM_BASE_URL = "https://ws.audioscrobbler.com/2.0/"

class LastFmService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.LASTFM_API_KEY and settings.LASTFM_API_KEY.strip())

    @staticmethod
    def _params_hash(params: Dict[str, Any]) -> str:
        s = json.dumps(params, sort_keys=True)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_response(cls, db: Session, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        p_hash = cls._params_hash(params)
        now = datetime.now(timezone.utc)
        cached = (
            db.query(ApiCache)
            .filter(
                ApiCache.source == "lastfm",
                ApiCache.endpoint == method,
                ApiCache.params_hash == p_hash
            )
            .first()
        )
        expires_at = cached.expires_at if cached else None
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if cached and expires_at and expires_at > now:
            return json.loads(cached.payload_json)
        return None

    @classmethod
    def save_cache_response(
        cls, db: Session, method: str, params: Dict[str, Any], status: int, data: Dict[str, Any], ttl_hours: int = 6
    ):
        p_hash = cls._params_hash(params)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)
        cached = (
            db.query(ApiCache)
            .filter(
                ApiCache.source == "lastfm",
                ApiCache.endpoint == method,
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
                source="lastfm",
                endpoint=method,
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
    def request(cls, db: Session, method: str, extra_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Queries Last.fm API with caching and error disclosures."""
        if not cls.is_configured():
            record_log("WARNING", f"Last.fm API key missing for method {method}")
            return {
                "error": "Last.fm API key not configured. Set LASTFM_API_KEY in .env.",
                "configured": False,
                "data": None
            }

        params = {"method": method, "api_key": settings.LASTFM_API_KEY, "format": "json"}
        if extra_params:
            params.update(extra_params)

        cache_lookup_params = {k: v for k, v in params.items() if k != "api_key"}
        cached_data = cls.get_cached_response(db, method, cache_lookup_params)
        if cached_data:
            cached_row = (
                db.query(ApiCache)
                .filter(
                    ApiCache.source == "lastfm",
                    ApiCache.endpoint == method,
                    ApiCache.params_hash == cls._params_hash(cache_lookup_params),
                )
                .first()
            )
            return {
                "configured": True,
                "data": cached_data,
                "source": "cache",
                "refreshed_at": cached_row.fetched_at.isoformat() if cached_row else None,
            }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(LASTFM_BASE_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and not data.get("error"):
                        cls.save_cache_response(db, method, cache_lookup_params, 200, data, ttl_hours=6)
                    record_log("INFO", f"Last.fm {method} fetch successful")
                    return {
                        "configured": True,
                        "data": data,
                        "source": "live",
                        "refreshed_at": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    record_log("ERROR", f"Last.fm API returned HTTP {resp.status_code}", details={"body": resp.text[:200]})
                    return {
                        "error": f"Last.fm returned HTTP {resp.status_code}: {resp.text[:150]}",
                        "configured": True,
                        "data": None
                    }
        except Exception as e:
            record_log("ERROR", f"Last.fm connection error: {str(e)}")
            return {"error": f"Connection to Last.fm failed: {str(e)}", "configured": True, "data": None}

    @classmethod
    def get_chart_top_tracks(cls, db: Session, limit: int = 30) -> Dict[str, Any]:
        """Fetches top global chart tracks from Last.fm."""
        res = cls.request(db, "chart.gettoptracks", {"limit": limit})
        if not res.get("configured") or not res.get("data"):
            return res
        
        raw_tracks = res["data"].get("tracks", {}).get("track", [])
        return {"configured": True, "tracks": raw_tracks, "source": res.get("source", "live")}

    @classmethod
    def get_genre_top_tracks(cls, db: Session, genre: str, limit: int = 50) -> Dict[str, Any]:
        """Fetches a Last.fm tag chart. Tag charts are provider rankings, not industry charts."""
        tag = " ".join(genre.strip().casefold().replace("_", " ").split())
        aliases = {
            "hip hop": "hip-hop",
            "rap": "hip-hop",
            "electronic music": "electronic",
            "rock music": "rock",
            "pop music": "pop",
        }
        tag = aliases.get(tag, tag)
        if not tag:
            return {"configured": cls.is_configured(), "tracks": [], "error": "Choose a genre tag."}

        method = "chart.gettoptracks" if tag in {"all", "all genres", "global"} else "tag.gettoptracks"
        params = {"limit": limit} if method == "chart.gettoptracks" else {"tag": tag, "limit": limit}
        response = cls.request(db, method, params)
        if not response.get("configured") or response.get("error"):
            return {**response, "tracks": []}

        data = response.get("data") or {}
        if data.get("error"):
            return {
                "configured": True,
                "tracks": [],
                "error": str(data.get("message") or "Last.fm could not return this genre chart."),
                "refreshed_at": response.get("refreshed_at"),
            }
        tracks = data.get("tracks", {}).get("track", [])
        if isinstance(tracks, dict):
            tracks = [tracks]
        if not isinstance(tracks, list):
            tracks = []
        return {
            "configured": True,
            "tracks": tracks,
            "source": response.get("source", "live"),
            "refreshed_at": response.get("refreshed_at"),
            "tag": tag,
        }
