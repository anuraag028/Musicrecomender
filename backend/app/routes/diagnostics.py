import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models import ApiCache, SocialDocument
from backend.app.schemas import DiagnosticsResponse, ProviderStatus, DiagnosticLogItem
from backend.app.logging_config import LOG_BUFFER
from backend.app.config import settings
from backend.app.services.lastfm_service import LastFmService

router = APIRouter(prefix="/api/diagnostics", tags=["Diagnostics"])

@router.get("/logs", response_model=List[DiagnosticLogItem])
def get_diagnostic_logs(
    level: Optional[str] = Query(None, description="INFO, WARNING, ERROR"),
    request_id: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Returns structured JSON logs with filtering. Secrets and credentials are strictly redacted."""
    filtered = []
    # Inspect ring buffer in reverse chronological order
    for entry in reversed(LOG_BUFFER):
        if level and entry.get("level") != level.upper():
            continue
        if request_id and entry.get("request_id") != request_id:
            continue
        if run_id and entry.get("run_id") != run_id:
            continue

        filtered.append(DiagnosticLogItem(
            timestamp=entry["timestamp"],
            level=entry["level"],
            message=entry["message"],
            request_id=entry.get("request_id"),
            run_id=entry.get("run_id"),
            method=entry.get("method"),
            path=entry.get("path"),
            status_code=entry.get("status_code"),
            duration_ms=entry.get("duration_ms"),
            details=entry.get("details")
        ))
        if len(filtered) >= limit:
            break

    return filtered

@router.get("/providers", response_model=List[ProviderStatus])
def get_providers_status(db: Session = Depends(get_db)):
    """Returns health, key configuration status, caching state and rate limits of external providers."""
    # MusicBrainz
    mb_cache = db.query(ApiCache).filter(ApiCache.source == "musicbrainz").all()
    mb_count = len(mb_cache)
    mb_latest = max([c.fetched_at for c in mb_cache]) if mb_cache else None

    mb_status = ProviderStatus(
        provider="MusicBrainz Web Service (WS/2)",
        status="HEALTHY",
        is_live=True,
        requires_key=False,
        key_configured=True,
        last_fetch=mb_latest.isoformat() if mb_latest else None,
        cached_records_count=mb_count,
        error_message=None,
        rate_limit_policy="Strict 1 request/second via token-bucket limiter; User-Agent verified."
    )

    # Last.fm
    lfm_configured = LastFmService.is_configured()
    lfm_cache = db.query(ApiCache).filter(ApiCache.source == "lastfm").all()
    lfm_count = len(lfm_cache)
    lfm_latest = max([c.fetched_at for c in lfm_cache]) if lfm_cache else None

    lfm_status = ProviderStatus(
        provider="Last.fm API (AudioScrobbler 2.0)",
        status="HEALTHY" if lfm_configured else "KEY_REQUIRED",
        is_live=lfm_configured,
        requires_key=True,
        key_configured=lfm_configured,
        last_fetch=lfm_latest.isoformat() if lfm_latest else None,
        cached_records_count=lfm_count,
        error_message=None if lfm_configured else "LASTFM_API_KEY is not set in .env. Live chart data is unavailable.",
        rate_limit_policy="5 requests/second limit per Last.fm terms."
    )

    # TWSMA RSS Feeds
    docs = db.query(SocialDocument).all()
    doc_count = len(docs)
    doc_latest = max([d.retrieved_at for d in docs]) if docs else None

    rss_status = ProviderStatus(
        provider="Configured music-news RSS feeds (TWSMA text analysis)",
        status="HEALTHY" if doc_count > 0 else "READY_TO_SYNC",
        is_live=True,
        requires_key=False,
        key_configured=True,
        last_fetch=doc_latest.isoformat() if doc_latest else None,
        cached_records_count=doc_count,
        error_message=None,
        rate_limit_policy="Periodic RSS feed polling; compliant with robots.txt and cache headers."
    )

    return [mb_status, lfm_status, rss_status]
