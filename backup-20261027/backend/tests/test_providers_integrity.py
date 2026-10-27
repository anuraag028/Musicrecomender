import json
from datetime import datetime, timezone
from backend.app.models import Track, SocialDocument
from backend.app.services.lastfm_service import LastFmService
from backend.app.services.catalogue_service import CatalogueService
from backend.app.services.youtube_service import YouTubeService
from backend.app.services.twsma_service import TwsmaService

def test_lastfm_missing_key_honest_state(test_db):
    # Ensure Last.fm service reports honest error when unconfigured
    result = LastFmService.request(test_db, "chart.gettoptracks")
    assert result["configured"] is False or "error" in result
    # Crucial test: Ensure 0 tracks were fabricated
    count = test_db.query(Track).count()
    assert count == 0

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

def test_playback_resolution_honesty(test_db):
    res = YouTubeService.resolve_video(test_db, "Radiohead", "Creep")
    assert "playback_provider" in res
    assert res["playback_provider"] == "youtube"
    # When no API key is provided, honest fallback is returned without pretending it is verified live
    if not YouTubeService.is_configured():
        assert res["status"] == "KEY_REQUIRED_FALLBACK"
        assert res["playback_verified"] is False
        assert "embed_url" in res

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
