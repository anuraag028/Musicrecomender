import json
import pytest
from backend.app.models import Track, DemoUser, Interaction
from backend.app.services.recommendation_engine import RecommendationEngine

def _seed_test_catalogue(test_db):
    tracks = [
        Track(
            id="t1",
            provider="musicbrainz",
            provider_id="mb-t1",
            title="Karma Police",
            artist="Radiohead",
            genres=json.dumps(["indie rock", "alternative rock"]),
            tags=json.dumps(["rock", "indie", "alternative", "britpop"]),
            listener_count=1500000,
            chart_rank=5,
            provenance_source="MusicBrainz API",
            playback_provider="youtube",
            playback_id="IBH97ma9Meg",
            playback_verified=True
        ),
        Track(
            id="t2",
            provider="musicbrainz",
            provider_id="mb-t2",
            title="Levitating",
            artist="Dua Lipa",
            genres=json.dumps(["pop", "disco"]),
            tags=json.dumps(["pop", "dance", "disco", "club"]),
            listener_count=2000000,
            chart_rank=1,
            provenance_source="MusicBrainz API",
            playback_provider="youtube",
            playback_id="TUVcZfQe-Kw",
            playback_verified=True
        ),
        Track(
            id="t3",
            provider="musicbrainz",
            provider_id="mb-t3",
            title="Resonance",
            artist="HOME",
            genres=json.dumps(["electronic", "synthwave"]),
            tags=json.dumps(["electronic", "synthwave", "chillwave", "ambient"]),
            listener_count=800000,
            chart_rank=12,
            provenance_source="MusicBrainz API",
            playback_provider="youtube",
            playback_id="8GW6sLrK40k",
            playback_verified=True
        )
    ]
    for t in tracks:
        test_db.add(t)
    test_db.commit()
    return tracks

def test_recommendation_math_and_weights_renormalization(test_db):
    _seed_test_catalogue(test_db)
    
    # Run recommendation for demo-user-1 (Alex - Indie)
    db_run, ranked_items, funnel = RecommendationEngine.generate_recommendations(
        db=test_db,
        user_id="demo-user-1",
        limit=5,
        exclude_played=False
    )

    trace = json.loads(db_run.trace_json)
    assert trace["run_id"] == db_run.run_id
    assert trace["user_id"] == "demo-user-1"
    
    # Check effective weights
    eff_w = trace["effective_weights"]
    total_weight = sum(eff_w.values())
    assert pytest.approx(total_weight, 0.01) == 1.0

    # Verify each ranked item
    assert len(ranked_items) > 0
    for itm in ranked_items:
        score = itm["final_score"]
        assert 0.0 <= score <= 1.0
        
        # Mathematical verification of hybrid contribution
        comp_contrib_sum = sum(
            c["weighted_contribution"]
            for c in itm["components"].values()
            if c.get("weighted_contribution") is not None
        )
        assert pytest.approx(score, 0.01) == comp_contrib_sum

def test_reproducibility_of_scores(test_db):
    _seed_test_catalogue(test_db)
    
    # Run 1
    _, items_1, _ = RecommendationEngine.generate_recommendations(
        db=test_db, user_id="demo-user-1", limit=3, exclude_played=False
    )
    # Run 2
    _, items_2, _ = RecommendationEngine.generate_recommendations(
        db=test_db, user_id="demo-user-1", limit=3, exclude_played=False
    )

    assert len(items_1) == len(items_2)
    for i1, i2 in zip(items_1, items_2):
        assert i1["track_id"] == i2["track_id"]
        assert pytest.approx(i1["final_score"], 0.0001) == i2["final_score"]

def test_cold_start_fallback_handling(test_db):
    _seed_test_catalogue(test_db)
    
    # Create a fresh cold-start demo user with 0 interactions
    cold_user = DemoUser(
        id="demo-cold-start",
        name="Cold Start User",
        label="SYNTHETIC / DEMO PROFILE",
        preferred_genres=json.dumps(["rock"])
    )
    test_db.add(cold_user)
    test_db.commit()

    db_run, ranked_items, funnel = RecommendationEngine.generate_recommendations(
        db=test_db, user_id="demo-cold-start", limit=3, exclude_played=False
    )

    trace = json.loads(db_run.trace_json)
    # Collaborative component should be transparently unavailable
    for itm in ranked_items:
        collab_comp = itm["components"]["collaborative"]
        assert collab_comp["available"] is False
        assert collab_comp["score"] is None
        assert "Cold-start" in collab_comp["reason"]
    
    # Effective weights must still sum to 1.0
    eff_w = trace["effective_weights"]
    assert pytest.approx(sum(eff_w.values()), 0.01) == 1.0
