import json
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import Track, Release
from backend.app.schemas import TrackBase, ReleaseItem, GenreChartResponse, GenreChartTrack
from backend.app.services.catalogue_service import CatalogueService
from backend.app.logging_config import record_log
from backend.app.services.lastfm_service import LastFmService
from backend.app.services.apple_catalogue_service import AppleCatalogueService

router = APIRouter(prefix="/api/music", tags=["Music"])

@router.get("/apple-search")
def search_apple_catalogue(q: str = Query(..., min_length=1, max_length=256), limit: int = Query(20, ge=1, le=50)):
    """Proxy official Apple catalogue metadata; preview audio is never downloaded or persisted."""
    return AppleCatalogueService.search_related(q, "", limit=limit)

def _track_to_schema(t: Track) -> TrackBase:
    # Older cached rows used generic stock art; do not present it as album artwork.
    image_url = t.image_url if t.image_url and "images.unsplash.com" not in t.image_url else None
    return TrackBase(
        id=t.id,
        provider=t.provider,
        provider_id=t.provider_id,
        title=t.title,
        artist=t.artist,
        album=t.album,
        release_date=t.release_date,
        genres=json.loads(t.genres or "[]"),
        tags=json.loads(t.tags or "[]"),
        play_count=t.play_count,
        listener_count=t.listener_count,
        duration_ms=t.duration_ms,
        image_url=image_url,
        playback_provider="catalogue_only",
        playback_id=None,
        playback_verified=False,
        is_trending=t.is_trending,
        chart_rank=t.chart_rank,
        provenance_source=t.provenance_source,
        fetched_at=t.fetched_at
    )

@router.get("/trending", response_model=List[TrackBase])
def get_trending_tracks(limit: int = Query(25, ge=1, le=50), db: Session = Depends(get_db)):
    """Returns real trending tracks with provenance source and chart rank."""
    tracks = (
        db.query(Track)
        .filter(Track.is_trending == True, Track.provider == "lastfm")
        .order_by(Track.chart_rank.asc().nullslast())
        .limit(limit)
        .all()
    )
    if not tracks:
        # Auto-sync real trending tracks if empty
        record_log("INFO", "Trending tracks empty in DB, triggering sync")
        tracks = CatalogueService.sync_trending(db, limit=limit)
        CatalogueService.seed_synthetic_interactions_if_empty(db)

    return [_track_to_schema(t) for t in tracks]

@router.get("/new-releases", response_model=List[ReleaseItem])
def get_new_releases(limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    """Returns genuine newly released recordings/albums with dates and provenance."""
    releases = db.query(Release).order_by(Release.fetched_at.desc()).limit(limit).all()
    if not releases:
        record_log("INFO", "Releases empty in DB, triggering sync from MusicBrainz")
        releases = CatalogueService.sync_new_releases(db, limit=limit)

    return [
        ReleaseItem(
            id=r.id,
            title=r.title,
            artist=r.artist,
            release_date=r.release_date,
            release_type=r.release_type,
            provider=r.provider,
            provider_id=r.provider_id,
            image_url=r.image_url if r.image_url and "images.unsplash.com" not in r.image_url else None,
            provenance_source=r.provenance_source,
            fetched_at=r.fetched_at
        )
        for r in releases
    ]

def _chart_count(value):
    try:
        return max(0, int(value)) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

@router.get("/genre-chart", response_model=GenreChartResponse)
def get_genre_chart(genre: str = Query(..., min_length=1, max_length=64), db: Session = Depends(get_db)):
    """Returns only tracks returned by Last.fm's global or selected tag chart."""
    normalized = " ".join(genre.strip().casefold().replace("_", " ").split())
    aliases = {"hip hop": "hip-hop", "rap": "hip-hop", "electronic music": "electronic", "rock music": "rock", "pop music": "pop"}
    normalized = aliases.get(normalized, normalized)
    response = LastFmService.get_genre_top_tracks(db, normalized, limit=50)
    provider_tracks = response.get("tracks", [])
    ranked = []
    seen = set()
    for index, item in enumerate(provider_tracks, start=1):
        if not isinstance(item, dict):
            continue
        title = item.get("name")
        artist_field = item.get("artist") or {}
        artist = artist_field.get("name") if isinstance(artist_field, dict) else artist_field
        if not isinstance(title, str) or not title.strip() or not isinstance(artist, str) or not artist.strip():
            continue

        # If Last.fm includes track-level tags, require a match. The tag chart endpoint
        # itself is the provider's genre relevance evidence when it does not.
        tags_field = item.get("toptags", item.get("tags"))
        if tags_field:
            tag_items = tags_field.get("tag", []) if isinstance(tags_field, dict) else tags_field
            if isinstance(tag_items, dict):
                tag_items = [tag_items]
            observed = [str(tag.get("name", "") if isinstance(tag, dict) else tag).casefold() for tag in tag_items]
            if observed and normalized not in {tag for tag in observed} and not any(normalized in tag or tag in normalized for tag in observed):
                continue

        key = (artist.casefold().strip(), title.casefold().strip())
        if key in seen:
            continue
        seen.add(key)
        attrs = item.get("@attr") if isinstance(item.get("@attr"), dict) else {}
        try:
            rank = int(attrs.get("rank", index))
        except (TypeError, ValueError):
            rank = index
        url = item.get("url")
        ranked.append(GenreChartTrack(
            rank=rank,
            title=title.strip(),
            artist=artist.strip(),
            play_count=_chart_count(item.get("playcount")),
            listener_count=_chart_count(item.get("listeners")),
            source_url=url if isinstance(url, str) and url.startswith("https://") else None,
        ))
        if len(ranked) == 10:
            break

    unavailable = bool(response.get("error")) or not response.get("configured")
    status = "unavailable" if unavailable else "ok" if ranked else "empty"
    display_genre = "All genres" if normalized in {"all", "all genres", "global"} else normalized.title()
    return GenreChartResponse(
        status=status,
        genre=display_genre,
        methodology=(
            "Last.fm global chart order." if normalized in {"all", "all genres", "global"}
            else f"Last.fm tag.getTopTracks order for the '{normalized}' tag. This is a provider tag chart, not an official industry chart."
        ),
        refreshed_at=response.get("refreshed_at"),
        error=response.get("error"),
        tracks=ranked,
    )

@router.get("/search", response_model=List[TrackBase])
def search_music(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    """Searches real catalogue tracks by title, artist, or tag."""
    tracks = CatalogueService.search_catalogue(db, query=q, limit=limit)
    return [_track_to_schema(t) for t in tracks]

@router.get("/{track_id}", response_model=TrackBase)
def get_track_detail(track_id: str, db: Session = Depends(get_db)):
    """Returns single track metadata and provenance."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found in catalogue.")
    return _track_to_schema(track)

@router.post("/sync")
def sync_catalogue_data(background_tasks: BackgroundTasks):
    """Triggers synchronisation of real catalogue tracks, charts, and new releases."""
    def _do_sync():
        from backend.app.database import SessionLocal
        bg_db = SessionLocal()
        try:
            CatalogueService.sync_trending(bg_db, limit=25)
            CatalogueService.sync_new_releases(bg_db, limit=20)
            CatalogueService.seed_synthetic_interactions_if_empty(bg_db)
        finally:
            bg_db.close()

    background_tasks.add_task(_do_sync)
    return {"status": "SYNC_STARTED", "message": "Catalogue synchronization scheduled in background."}
