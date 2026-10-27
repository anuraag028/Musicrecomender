import json
import hashlib
import urllib.parse
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import ApiCache, Track
from backend.app.logging_config import record_log

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

class YouTubeService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.YOUTUBE_API_KEY and settings.YOUTUBE_API_KEY.strip())

    @classmethod
    def resolve_video(cls, db: Session, artist: str, title: str) -> Dict[str, Any]:
        """
        Resolves YouTube playback reference for a track.
        Validates embeddability and distinguishes verified official video vs search embed fallback.
        """
        query = f"{artist} {title} official audio"
        cache_key = hashlib.sha256(f"{artist.lower()}||{title.lower()}".encode("utf-8")).hexdigest()

        # Check existing cached resolution
        cached = (
            db.query(ApiCache)
            .filter(
                ApiCache.source == "youtube",
                ApiCache.endpoint == "search",
                ApiCache.params_hash == cache_key
            )
            .first()
        )
        if cached:
            payload = json.loads(cached.payload_json)
            return payload

        if not cls.is_configured():
            # Honest unverified fallback: YouTube search embed query
            safe_query = urllib.parse.quote(f"{artist} - {title}")
            result = {
                "playback_id": None,
                "embed_url": f"https://www.youtube-nocookie.com/embed?listType=search&list={safe_query}",
                "playback_provider": "youtube",
                "playback_verified": False,
                "source": "fallback_search_embed",
                "status": "KEY_REQUIRED_FALLBACK",
                "note": "YOUTUBE_API_KEY is not configured in .env. Playing via YouTube Search Embed fallback."
            }
            return result

        # Query YouTube Data API v3
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoEmbeddable": "true",
            "maxResults": 3,
            "key": settings.YOUTUBE_API_KEY
        }

        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(YOUTUBE_SEARCH_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if items:
                        first_item = items[0]
                        video_id = first_item.get("id", {}).get("videoId")
                        snippet = first_item.get("snippet", {})
                        video_title = snippet.get("title", "")
                        channel_title = snippet.get("channelTitle", "")

                        result = {
                            "playback_id": video_id,
                            "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?enablejsapi=1&origin=http://localhost:5173",
                            "playback_provider": "youtube",
                            "playback_verified": True,
                            "resolved_title": video_title,
                            "channel_title": channel_title,
                            "source": "youtube_data_api_v3",
                            "status": "VERIFIED"
                        }

                        # Save to cache
                        cache_entry = ApiCache(
                            source="youtube",
                            endpoint="search",
                            params_hash=cache_key,
                            response_status=200,
                            payload_json=json.dumps(result),
                            fetched_at=datetime.now(timezone.utc),
                            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
                            is_stale=False
                        )
                        db.add(cache_entry)
                        db.commit()
                        record_log("INFO", f"Resolved YouTube video for {artist} - {title}: {video_id}")
                        return result
                    else:
                        result = {
                            "playback_id": None,
                            "playback_provider": "youtube",
                            "playback_verified": False,
                            "source": "youtube_data_api_v3",
                            "status": "NO_EMBEDDABLE_VIDEO_FOUND",
                            "note": "No embeddable video found for this query."
                        }
                        return result
                else:
                    record_log("ERROR", f"YouTube Data API error HTTP {resp.status_code}: {resp.text[:150]}")
                    return {
                        "playback_id": None,
                        "playback_provider": "youtube",
                        "playback_verified": False,
                        "status": "API_ERROR",
                        "error": f"YouTube API error HTTP {resp.status_code}"
                    }
        except Exception as e:
            record_log("ERROR", f"YouTube resolution exception: {str(e)}")
            return {
                "playback_id": None,
                "playback_provider": "youtube",
                "playback_verified": False,
                "status": "CONNECTION_FAILED",
                "error": str(e)
            }
