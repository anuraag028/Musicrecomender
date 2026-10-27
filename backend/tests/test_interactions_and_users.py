import json
from backend.app.models import Track, Interaction
from backend.app.services.recommendation_engine import RecommendationEngine

def _seed_catalogue(test_db):
    t_rock = Track(
        id="t-rock-1",
        provider="musicbrainz",
        provider_id="mb-rock",
        title="Creep",
        artist="Radiohead",
        genres=json.dumps(["indie rock", "grunge"]),
        tags=json.dumps(["rock", "indie", "90s"]),
        provenance_source="MusicBrainz WS/2",
        playback_provider="youtube",
        playback_id="XFkzRNyygfk",
        playback_verified=True
    )
    t_pop = Track(
        id="t-pop-1",
        provider="musicbrainz",
        provider_id="mb-pop",
        title="Don't Start Now",
        artist="Dua Lipa",
        genres=json.dumps(["pop", "disco"]),
        tags=json.dumps(["dance", "pop", "nu-disco"]),
        provenance_source="MusicBrainz WS/2",
        playback_provider="youtube",
        playback_id="oygrmJFKYZY",
        playback_verified=True
    )
    test_db.add(t_rock)
    test_db.add(t_pop)
    test_db.commit()
    return t_rock, t_pop

def test_demo_users_preference_distinction(test_db):
    t_rock, t_pop = _seed_catalogue(test_db)

    # Seed synthetic likes
    test_db.add(Interaction(user_id="demo-user-1", track_id=t_rock.id, interaction_type="like", weight=1.0, is_synthetic_seed=True))
    test_db.add(Interaction(user_id="demo-user-2", track_id=t_pop.id, interaction_type="like", weight=1.0, is_synthetic_seed=True))
    test_db.commit()

    # User 1 (Alex - Indie)
    _, items_user1, _ = RecommendationEngine.generate_recommendations(
        db=test_db, user_id="demo-user-1", limit=2, exclude_played=False
    )
    # User 2 (Beatrix - Pop)
    _, items_user2, _ = RecommendationEngine.generate_recommendations(
        db=test_db, user_id="demo-user-2", limit=2, exclude_played=False
    )

    # User 1 top recommendation should be Rock track
    assert items_user1[0]["track_id"] == t_rock.id
    # User 2 top recommendation should be Pop track
    assert items_user2[0]["track_id"] == t_pop.id

def test_interaction_persists_and_excludes(client, test_db):
    t_rock, _ = _seed_catalogue(test_db)

    # Record skip interaction via API
    payload = {
        "user_id": "demo-user-1",
        "track_id": t_rock.id,
        "interaction_type": "skip"
    }
    resp = client.post("/api/interactions", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["interaction_type"] == "skip"
    assert data["weight"] == -0.5
    assert data["is_synthetic_seed"] is False

    # Verify track is excluded from recommendations when user disliked it
    gen_resp = client.post("/api/recommendations/generate", json={"user_id": "demo-user-1", "limit": 5})
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    track_ids = [t["track_id"] for t in gen_data["tracks"]]
    assert t_rock.id not in track_ids
    assert gen_data["funnel"]["excluded_disliked"] >= 1

def test_invalid_requests_handled(client, test_db):
    t_rock, _ = _seed_catalogue(test_db)

    # Invalid user ID
    resp = client.post("/api/recommendations/generate", json={"user_id": "non-existent-user", "limit": 5})
    assert resp.status_code == 400
    assert "detail" in resp.json()

    # Rate interaction without rating_value on existing track
    resp = client.post("/api/interactions", json={"user_id": "demo-user-1", "track_id": t_rock.id, "interaction_type": "rate"})
    assert resp.status_code == 400
    assert "rating_value is required" in resp.json()["detail"]
