import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models import DemoUser, Interaction, Track
from backend.app.schemas import DemoUserProfile, UserPreferencesResponse
from backend.app.services.catalogue_service import CatalogueService

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("", response_model=List[DemoUserProfile])
def get_demo_users(db: Session = Depends(get_db)):
    """Returns the 3 distinctly configured demo profiles with interaction counts."""
    users = db.query(DemoUser).all()
    results = []
    for u in users:
        count = db.query(Interaction).filter(Interaction.user_id == u.id).count()
        results.append(DemoUserProfile(
            id=u.id,
            name=u.name,
            label=u.label,
            bio=u.bio,
            avatar=u.avatar,
            preferred_genres=json.loads(u.preferred_genres or "[]"),
            interaction_count=count,
            created_at=u.created_at
        ))
    return results

@router.get("/{user_id}/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(user_id: str, db: Session = Depends(get_db)):
    """Returns preferences and recent interaction history for selected user."""
    user = db.query(DemoUser).filter(DemoUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")

    interactions = (
        db.query(Interaction)
        .filter(Interaction.user_id == user_id)
        .order_by(Interaction.created_at.desc())
        .limit(20)
        .all()
    )

    interaction_list = []
    stats = {"likes": 0, "dislikes": 0, "skips": 0, "plays": 0, "ratings": 0}

    for i in interactions:
        t = i.track
        interaction_list.append({
            "id": i.id,
            "track_id": i.track_id,
            "title": t.title if t else "Unknown Title",
            "artist": t.artist if t else "Unknown Artist",
            "interaction_type": i.interaction_type,
            "weight": i.weight,
            "rating_value": i.rating_value,
            "is_synthetic_seed": i.is_synthetic_seed,
            "created_at": i.created_at.isoformat()
        })
        if i.interaction_type == "like":
            stats["likes"] += 1
        elif i.interaction_type == "dislike":
            stats["dislikes"] += 1
        elif i.interaction_type == "skip":
            stats["skips"] += 1
        elif i.interaction_type == "play":
            stats["plays"] += 1
        elif i.interaction_type == "rate":
            stats["ratings"] += 1

    return UserPreferencesResponse(
        user_id=user.id,
        name=user.name,
        label=user.label,
        preferred_genres=json.loads(user.preferred_genres or "[]"),
        recent_interactions=interaction_list,
        stats=stats
    )

@router.post("/reset-demo")
def reset_demo_profiles(db: Session = Depends(get_db)):
    """Re-initializes demo profiles and synthetic seed interactions without wiping catalogue."""
    CatalogueService.ensure_demo_users(db)
    # Clear only synthetic interactions
    db.query(Interaction).filter(Interaction.is_synthetic_seed == True).delete()
    db.commit()
    CatalogueService.seed_synthetic_interactions_if_empty(db)
    return {"status": "SUCCESS", "message": "Demo profiles and synthetic seed interactions refreshed."}
