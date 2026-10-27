from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.database import get_db
from backend.app.models import Interaction, DemoUser, Track
from backend.app.schemas import InteractionCreate, InteractionResponse
from backend.app.logging_config import record_log

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])

WEIGHT_MAP = {
    "like": 1.0,
    "dislike": -1.0,
    "skip": -0.5,
    "play": 0.5,
}

@router.post("", response_model=InteractionResponse)
def record_user_interaction(data: InteractionCreate, db: Session = Depends(get_db)):
    """Records user action (like, dislike, skip, play, rate) and updates interaction matrix."""
    user = db.query(DemoUser).filter(DemoUser.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{data.user_id}' does not exist.")

    track = db.query(Track).filter(Track.id == data.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail=f"Track '{data.track_id}' not found in catalogue.")

    itype = data.interaction_type.lower()
    if itype == "rate":
        if data.rating_value is None:
            raise HTTPException(status_code=400, detail="rating_value is required for 'rate' interaction type.")
        calc_weight = round(data.rating_value / 5.0, 3)
    elif itype in WEIGHT_MAP:
        calc_weight = WEIGHT_MAP[itype]
    else:
        raise HTTPException(status_code=400, detail=f"Invalid interaction_type '{itype}'. Valid: like, dislike, skip, play, rate.")

    # Record interaction (marked as live session, not synthetic seed)
    interaction = Interaction(
        user_id=data.user_id,
        track_id=data.track_id,
        interaction_type=itype,
        rating_value=data.rating_value,
        weight=calc_weight,
        is_synthetic_seed=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    record_log(
        "INFO",
        f"Recorded {itype} for user {data.user_id} on track {track.artist} - {track.title}",
        details={"interaction_id": interaction.id, "weight": calc_weight}
    )

    return InteractionResponse(
        id=interaction.id,
        user_id=interaction.user_id,
        track_id=interaction.track_id,
        interaction_type=interaction.interaction_type,
        rating_value=interaction.rating_value,
        weight=interaction.weight,
        is_synthetic_seed=interaction.is_synthetic_seed,
        created_at=interaction.created_at,
        message=f"Interaction '{itype}' recorded successfully."
    )
