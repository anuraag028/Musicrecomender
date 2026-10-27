import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.app.database import get_db
from backend.app.models import RecommendationRun
from backend.app.schemas import (
    RecommendationGenerateRequest,
    RecommendationGenerateResponse,
    RecommendationRunTrace,
    CandidateFunnel,
    RankedTrackExplainability,
    SeedRecommendationRequest,
)
from backend.app.services.recommendation_engine import RecommendationEngine
from backend.app.services.seed_recommendation_service import SeedRecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

@router.post("/seeded")
def generate_seeded_recommendations(data: SeedRecommendationRequest, db: Session = Depends(get_db)):
    """Seed-first hybrid recommendations for For You and the smart queue; demo profiles are excluded."""
    try:
        return SeedRecommendationService.generate(
            db,
            title=data.seed_title or "",
            artist=data.seed_artist or "",
            album=data.seed_album or "",
            genre=data.seed_genre or "",
            limit=data.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Seed recommendation error: {str(exc)}")

@router.post("/generate", response_model=RecommendationGenerateResponse)
def generate_recommendations(data: RecommendationGenerateRequest, db: Session = Depends(get_db)):
    """Executes hybrid recommendation pipeline for user, returns ranked tracks and funnel."""
    try:
        db_run, ranked_items, funnel_dict = RecommendationEngine.generate_recommendations(
            db=db,
            user_id=data.user_id,
            limit=data.limit,
            diversity_penalty=data.diversity_penalty,
            exclude_played=data.exclude_played,
            custom_weights=data.custom_weights,
            seed_title=data.seed_title,
            seed_artist=data.seed_artist,
            seed_genre=data.seed_genre,
        )

        trace_data = json.loads(db_run.trace_json)
        effective_w = trace_data.get("effective_weights", {})

        return RecommendationGenerateResponse(
            run_id=db_run.run_id,
            user_id=db_run.user_id,
            generated_at=db_run.created_at.isoformat(),
            count=len(ranked_items),
            effective_weights=effective_w,
            tracks=[RankedTrackExplainability(**item) for item in ranked_items],
            funnel=CandidateFunnel(**funnel_dict),
            trace_url=f"/api/recommendations/{db_run.run_id}/trace"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")

@router.get("/latest/trace", response_model=RecommendationRunTrace)
def get_latest_trace(db: Session = Depends(get_db)):
    """Returns the full numeric explainability trace of the most recent recommendation run."""
    latest_run = db.query(RecommendationRun).order_by(RecommendationRun.created_at.desc()).first()
    if not latest_run:
        raise HTTPException(status_code=404, detail="No recommendation runs have been executed yet.")
    return json.loads(latest_run.trace_json)

@router.get("/{run_id}/trace", response_model=RecommendationRunTrace)
def get_recommendation_trace(run_id: str, db: Session = Depends(get_db)):
    """Returns full reproducible numeric explainability trace for specific run_id."""
    run = db.query(RecommendationRun).filter(RecommendationRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Recommendation run '{run_id}' not found.")
    return json.loads(run.trace_json)
