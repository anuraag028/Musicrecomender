from typing import Any, Dict, List
from urllib.parse import urlparse, urlunparse

import httpx

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"


def _trusted_https_url(value: Any, suffixes: tuple[str, ...]) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme not in {"http", "https"} or not any(host == suffix or host.endswith("." + suffix) for suffix in suffixes):
        return None
    # Apple documents some legacy HTTP sample URLs; promote trusted Apple hosts to HTTPS.
    return urlunparse(("https", parsed.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


class AppleCatalogueService:
    """Small, non-persistent proxy for official iTunes Search API metadata."""

    @classmethod
    def search_related(cls, title: str, artist: str, genre: str | None = None, limit: int = 50) -> Dict[str, Any]:
        term = " ".join(value.strip() for value in (artist, title, genre or "") if value and value.strip())
        try:
            with httpx.Client(timeout=5.0, headers={"User-Agent": "MelodyMusicRecommender/1.0"}) as client:
                response = client.get(ITUNES_SEARCH_URL, params={"term": term, "entity": "song", "limit": min(max(limit, 1), 50)})
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": "unavailable", "error": f"Apple catalogue unavailable: {exc}", "retrieved_at": None, "tracks": []}

        raw = payload.get("results", []) if isinstance(payload, dict) else []
        tracks: List[Dict[str, Any]] = []
        seen = set()
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            track_title = item.get("trackName")
            track_artist = item.get("artistName")
            track_id = item.get("trackId")
            if not isinstance(track_title, str) or not track_title.strip() or not isinstance(track_artist, str) or not track_artist.strip():
                continue
            key = (" ".join(track_artist.casefold().split()), " ".join(track_title.casefold().split()))
            if key in seen:
                continue
            seen.add(key)
            preview = _trusted_https_url(item.get("previewUrl"), ("apple.com", "mzstatic.com"))
            store_url = _trusted_https_url(item.get("trackViewUrl"), ("apple.com",))
            artwork = _trusted_https_url(item.get("artworkUrl100"), ("mzstatic.com", "apple.com"))
            tracks.append({
                "id": f"itunes-{track_id}" if track_id is not None else f"itunes-{len(tracks)}",
                "provider_id": str(track_id) if track_id is not None else None,
                "title": track_title.strip(),
                "artist": track_artist.strip(),
                "album": item.get("collectionName") if isinstance(item.get("collectionName"), str) else None,
                "genre": item.get("primaryGenreName") if isinstance(item.get("primaryGenreName"), str) else None,
                "duration_ms": item.get("trackTimeMillis") if isinstance(item.get("trackTimeMillis"), int) else None,
                "image_url": artwork,
                "preview_url": preview,
                "store_url": store_url,
                "source": "Apple iTunes",
            })
        from datetime import datetime, timezone
        return {"status": "ok" if tracks else "empty", "error": None, "retrieved_at": datetime.now(timezone.utc).isoformat(), "tracks": tracks}
