import json
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import Track, Release
from backend.app.schemas import TrackBase, ReleaseItem
from backend.app.services.catalogue_service import CatalogueService
from backend.app.services.youtube_service import YouTubeService
from backend.app.logging_config import record_log

router = APIRouter(prefix="/api/music", tags=["Music"])

def _track_to_schema(t: Track) -> TrackBase:
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
        image_url=t.image_url,
        playback_provider=t.playback_provider or "youtube",
        playback_id=t.playback_id,
        playback_verified=t.playback_verified,
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
        .filter(Track.is_trending == True)
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
            image_url=r.image_url,
            provenance_source=r.provenance_source,
            fetched_at=r.fetched_at
        )
        for r in releases
    ]

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

@router.get("/{track_id}/playback")
def get_track_playback(track_id: str, db: Session = Depends(get_db)):
    """Resolves and returns legitimate playback embed reference for track."""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found.")

    res = YouTubeService.resolve_video(db, track.artist, track.title)
    if res.get("playback_id") and not track.playback_id:
        track.playback_id = res["playback_id"]
        track.playback_verified = res.get("playback_verified", False)
        db.commit()

    return {
        "track_id": track.id,
        "title": track.title,
        "artist": track.artist,
        "playback_provider": res.get("playback_provider", "youtube"),
        "playback_id": res.get("playback_id") or track.playback_id,
        "embed_url": res.get("embed_url"),
        "playback_verified": res.get("playback_verified", False),
        "source": res.get("source"),
        "status": res.get("status"),
        "note": res.get("note")
    }

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
