from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from backend.app.database import get_db
from backend.app.models import Track, DemoUser, Interaction

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint confirming database connectivity and state."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    track_count = db.query(Track).count() if db_ok else 0
    demo_user_count = db.query(DemoUser).count() if db_ok else 0
    interaction_count = db.query(Interaction).count() if db_ok else 0

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "tracks_in_catalogue": track_count,
        "demo_profiles_count": demo_user_count,
        "total_interactions": interaction_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
