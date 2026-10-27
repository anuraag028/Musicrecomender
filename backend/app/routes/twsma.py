from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import TwsmaSummary
from backend.app.services.twsma_service import TwsmaService

router = APIRouter(prefix="/api/twsma", tags=["TWSMA Analytics"])

@router.get("/summary", response_model=TwsmaSummary)
def get_twsma_summary(db: Session = Depends(get_db)):
    """Returns real text analytics metrics, sentiment distributions, and vocabulary from music news."""
    summary_data = TwsmaService.get_summary(db)
    return summary_data

@router.post("/sync")
def sync_twsma_feeds(db: Session = Depends(get_db)):
    """Triggers ingestion and NLP processing of permitted RSS music news feeds."""
    res = TwsmaService.sync_news_feed(db)
    return res

@router.get("/context")
def get_contextual_news(
    artist: str = Query("", max_length=256),
    title: str = Query("", max_length=256),
    album: str = Query("", max_length=256),
    genre: str = Query("", max_length=128),
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """Return actual RSS articles ranked by exact mentions of the currently playing track context."""
    return TwsmaService.get_context_articles(db, artist=artist, title=title, album=album, genre=genre, limit=limit)
