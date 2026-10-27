import json
from datetime import datetime, timezone
from backend.app.models import Track, SocialDocument
from backend.app.services.lastfm_service import LastFmService
from backend.app.services.catalogue_service import CatalogueService
from backend.app.services.twsma_service import TwsmaService
from backend.app.services.recommendation_engine import RecommendationEngine

def test_lastfm_missing_key_honest_state(test_db):
    # Ensure Last.fm service reports honest error when unconfigured
    result = LastFmService.request(test_db, "chart.gettoptracks")
    assert result["configured"] is False or "error" in result
    # Crucial test: Ensure 0 tracks were fabricated
    count = test_db.query(Track).count()
    assert count == 0

def test_genre_chart_uses_lastfm_tag_chart_and_returns_only_provider_tracks(client, monkeypatch):
    calls = []
    raw = [
        {"name": "Verified Song", "artist": {"name": "Known Artist"}, "playcount": "1234", "listeners": "567", "url": "https://www.last.fm/music/Known+Artist/Verified+Song", "@attr": {"rank": "3"}},
        {"name": "Wrong Tag Song", "artist": {"name": "Other Artist"}, "toptags": {"tag": [{"name": "metal"}]}},
        {"name": "Missing Artist"},
    ]
    def fake_request(cls, db, method, extra_params=None):
        calls.append((method, extra_params))
        return {"configured": True, "data": {"tracks": {"track": raw}}, "source": "live", "refreshed_at": "2026-10-27T00:00:00+00:00"}
    monkeypatch.setattr(LastFmService, "request", classmethod(fake_request))

    response = client.get("/api/music/genre-chart?genre=hip-hop")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["genre"] == "Hip-Hop"
    assert len(payload["tracks"]) == 1
    assert payload["tracks"][0] == {
        "rank": 3,
        "title": "Verified Song",
        "artist": "Known Artist",
        "play_count": 1234,
        "listener_count": 567,
        "source_url": "https://www.last.fm/music/Known+Artist/Verified+Song",
    }
    assert calls == [("tag.gettoptracks", {"tag": "hip-hop", "limit": 50})]

def test_genre_chart_unavailable_and_empty_results_are_explicit(client, monkeypatch):
    monkeypatch.setattr(LastFmService, "request", classmethod(lambda cls, db, method, extra_params=None: {
        "configured": False, "error": "Last.fm API key not configured. Set LASTFM_API_KEY in .env.", "data": None
    }))
    unavailable = client.get("/api/music/genre-chart?genre=pop").json()
    assert unavailable["status"] == "unavailable"
    assert unavailable["tracks"] == []
    assert "API key" in unavailable["error"]

    monkeypatch.setattr(LastFmService, "request", classmethod(lambda cls, db, method, extra_params=None: {
        "configured": True, "data": {"tracks": {"track": []}}, "source": "live", "refreshed_at": "2026-10-27T00:00:00+00:00"
    }))
    empty = client.get("/api/music/genre-chart?genre=pop").json()
    assert empty["status"] == "empty"
    assert empty["tracks"] == []

def test_lastfm_successful_tag_chart_is_cached_by_tag(test_db):
    params = {"tag": "bollywood", "limit": 50, "format": "json"}
    response = {"tracks": {"track": [{"name": "Returned by provider"}]}}
    LastFmService.save_cache_response(test_db, "tag.gettoptracks", params, 200, response, ttl_hours=6)
    cached = LastFmService.get_cached_response(test_db, "tag.gettoptracks", params)
    assert cached == response

def test_recommendations_accept_chart_seed_and_do_not_treat_musicbrainz_as_a_chart(test_db):
    _seed_recommendation_test_tracks(test_db)
    _, items, funnel = RecommendationEngine.generate_recommendations(
        db=test_db,
        user_id="demo-user-1",
        limit=10,
        exclude_played=False,
        seed_title="Blinding Lights",
        seed_artist="The Weeknd",
        seed_genre="pop",
    )
    assert funnel["retrieved"] == 3
    assert funnel["excluded_genre"] == 2
    assert funnel["scored"] == 1
    assert items[0]["title"] == "Levitating"
    assert items[0]["components"]["content"]["available"] is True
    assert items[0]["components"]["trend"]["available"] is False
    assert items[0]["components"]["text"]["available"] is False

def test_trend_score_requires_lastfm_provenance():
    musicbrainz_track = Track(id="mb", provider="musicbrainz", provider_id="mb", title="Song", artist="Artist", listener_count=500, chart_rank=1, provenance_source="MusicBrainz")
    lastfm_track = Track(id="lfm", provider="lastfm", provider_id="lfm", title="Song", artist="Artist", listener_count=500, chart_rank=1, provenance_source="Last.fm Global Chart")
    scores = RecommendationEngine._compute_trend_scores([musicbrainz_track, lastfm_track])
    assert scores["mb"]["available"] is False
    assert scores["lfm"]["available"] is True
    assert scores["lfm"]["score"] == 1.0

def _seed_recommendation_test_tracks(test_db):
    from backend.tests.test_recommendation_math import _seed_test_catalogue
    return _seed_test_catalogue(test_db)

def test_track_deduplication(test_db):
    rec_sample = {
        "id": "mbid-12345",
        "title": "Paranoid Android",
        "artist-credit": [{"name": "Radiohead", "joinphrase": ""}],
        "tags": [{"name": "rock"}, {"name": "alternative"}],
        "length": 387000
    }
    # Ingest once
    t1 = CatalogueService.ingest_musicbrainz_recording(test_db, rec_sample)
    assert t1 is not None
    assert test_db.query(Track).count() == 1

    # Ingest again with same ID
    t2 = CatalogueService.ingest_musicbrainz_recording(test_db, rec_sample)
    assert t2.id == t1.id
    assert test_db.query(Track).count() == 1

    # Ingest with different MBID but identical artist and title
    rec_sample_diff_id = {
        "id": "mbid-67890",
        "title": "paranoid android ",
        "artist-credit": [{"name": "Radiohead", "joinphrase": ""}],
        "tags": [{"name": "alternative rock"}]
    }
    t3 = CatalogueService.ingest_musicbrainz_recording(test_db, rec_sample_diff_id)
    assert t3.id == t1.id
    assert test_db.query(Track).count() == 1

def test_catalogue_tracks_are_metadata_only(test_db):
    recording = {
        "id": "metadata-only-123",
        "title": "Creep",
        "artist-credit": [{"name": "Radiohead", "joinphrase": ""}],
    }
    track = CatalogueService.ingest_musicbrainz_recording(test_db, recording)
    assert track is not None
    assert track.playback_provider == "catalogue_only"
    assert track.playback_id is None
    assert track.playback_verified is False

def test_catalogue_search_ranks_exact_recording_first():
    exact = Track(id="exact", provider="musicbrainz", provider_id="exact", title="Blinding Lights", artist="The Weeknd", provenance_source="MusicBrainz")
    partial = Track(id="partial", provider="musicbrainz", provider_id="partial", title="Blinding Lights (Live)", artist="Another Artist", provenance_source="MusicBrainz")
    ranked = CatalogueService._rank_search_results([partial, exact], "Blinding Lights", "The Weeknd")
    assert [track.id for track in ranked] == ["exact", "partial"]

def test_twsma_text_processing():
    sample_text = "<p>The indie rock band announced an exceptional, brilliant album release today.</p>"
    cleaned = TwsmaService.clean_text(sample_text)
    assert "<p>" not in cleaned
    tokens = TwsmaService.tokenize(cleaned)
    assert "indie" in tokens
    assert "the" not in tokens  # Stopword removed

def test_twsma_signal_calculation_empty_vs_populated(test_db):
    # Empty documents
    res_empty = TwsmaService.calculate_text_signal_for_artist(test_db, "Radiohead", "Creep")
    assert res_empty["available"] is False
    assert res_empty["score"] is None

    # Insert genuine article
    doc = SocialDocument(
        source_name="Pitchfork News",
        source_url="https://example.com/pitchfork-radiohead",
        title="Radiohead share rare live performance video",
        summary="Radiohead released an incredible new archival live session that fans love.",
        tokens_json=json.dumps(["radiohead", "live", "performance", "incredible"]),
        sentiment_compound=0.85,
        sentiment_label="positive",
        retrieved_at=datetime.now(timezone.utc)
    )
    test_db.add(doc)
    test_db.commit()

    res_found = TwsmaService.calculate_text_signal_for_artist(test_db, "Radiohead", "Creep")
    assert res_found["available"] is True
    assert res_found["score"] is not None
    assert 0.0 <= res_found["score"] <= 1.0
    assert len(res_found["evidence"]) > 0
