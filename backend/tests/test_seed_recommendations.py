import json
from datetime import datetime, timezone

import pytest

from backend.app.models import DemoUser, Interaction, SocialDocument, Track
from backend.app.services.apple_catalogue_service import AppleCatalogueService
from backend.app.services.seed_recommendation_service import SeedRecommendationService
from backend.app.services.twsma_service import TwsmaService
from backend.app.config import settings


def add_track(db, track_id, title, artist, genres=None, provider="musicbrainz", source="MusicBrainz"):
    item = Track(
        id=track_id, provider=provider, provider_id=track_id, title=title, artist=artist,
        album="Test Album", genres=json.dumps(genres or []), tags=json.dumps(genres or []),
        provenance_source=source, fetched_at=datetime.now(timezone.utc),
    )
    db.add(item)
    db.commit()
    return item


def test_seeded_recommendations_exclude_seed_dedupe_and_normalize_weights(test_db, monkeypatch):
    seed = add_track(test_db, "seed", "Blue Monday", "New Order", ["synth-pop", "electronic"])
    add_track(test_db, "duplicate-seed", "Blue Monday", "New Order", ["electronic"])
    add_track(test_db, "candidate-a", "Temptation", "New Order", ["synth-pop"])
    monkeypatch.setattr(AppleCatalogueService, "search_related", classmethod(lambda cls, *args, **kwargs: {
        "status": "ok", "error": None, "retrieved_at": "2026-10-27T00:00:00+00:00", "tracks": [
            {"id": "apple-duplicate", "provider_id": "123", "title": "Temptation", "artist": "New Order",
             "album": "Apple Album", "genre": "synth-pop", "image_url": None,
             "preview_url": "https://audio-ssl.itunes.apple.com/sample.m4a",
             "store_url": "https://music.apple.com/song/123"},
            {"id": "apple-seed", "provider_id": "124", "title": "Blue Monday", "artist": "New Order",
             "album": "Substance", "genre": "electronic", "image_url": None,
             "preview_url": "https://audio-ssl.itunes.apple.com/seed.m4a",
             "store_url": "https://music.apple.com/song/124"},
            {"id": "apple-related", "provider_id": "125", "title": "Confusion", "artist": "New Order",
             "album": "Movement", "genre": "electronic", "image_url": None,
             "preview_url": None, "store_url": "https://music.apple.com/song/125"},
        ],
    }))

    result = SeedRecommendationService.generate(test_db, title=seed.title, artist=seed.artist, genre="electronic")

    keys = [(track["artist"].casefold(), track["title"].casefold()) for track in result["tracks"]]
    assert ("new order", "blue monday") not in keys
    assert len(keys) == len(set(keys))
    assert result["apple_status"] == "ok"
    assert any(track["id"] == "apple-related" for track in result["tracks"])
    assert all(sum(track["effective_weights"].values()) == pytest.approx(1.0) for track in result["tracks"])
    assert result["collaborative_status"].startswith("Limited")
    assert all(not track["components"]["collaborative"]["available"] for track in result["tracks"])
    assert all(track["playback_availability"] in {"preview", "metadata_only"} for track in result["tracks"])


def test_synthetic_interactions_do_not_create_collaborative_evidence(test_db):
    seed = add_track(test_db, "seed", "Song One", "Artist One", ["rock"])
    candidate = add_track(test_db, "candidate", "Song Two", "Artist One", ["rock"])
    user = test_db.query(DemoUser).first()
    test_db.add_all([
        Interaction(user_id=user.id, track_id=seed.id, interaction_type="like", weight=1, is_synthetic_seed=True),
        Interaction(user_id=user.id, track_id=candidate.id, interaction_type="like", weight=1, is_synthetic_seed=True),
    ])
    test_db.commit()

    score = SeedRecommendationService._collaborative_scores(test_db, seed, [candidate])[candidate.id]
    assert not score["available"]
    assert "real" in score["reason"]


def test_real_seed_linked_interactions_enable_collaborative_signal(test_db):
    seed = add_track(test_db, "seed", "Song One", "Artist One", ["rock"])
    candidate = add_track(test_db, "candidate", "Song Two", "Artist Two", ["rock"])
    user = test_db.query(DemoUser).first()
    test_db.add_all([
        Interaction(user_id=user.id, track_id=seed.id, interaction_type="like", weight=1, is_synthetic_seed=False),
        Interaction(user_id=user.id, track_id=candidate.id, interaction_type="play", weight=.5, is_synthetic_seed=False),
    ])
    test_db.commit()

    score = SeedRecommendationService._collaborative_scores(test_db, seed, [candidate])[candidate.id]
    assert score["available"]
    assert score["score"] == .5
    assert score["evidence"][0]["matching_candidate_users"] == 1


def test_twsma_context_ranks_exact_entities_and_has_honest_empty_state(test_db):
    now = datetime.now(timezone.utc)
    test_db.add_all([
        SocialDocument(source_name="Example News", source_url="https://example.com/song",
                       title="Blue Monday returns", summary="New Order announce an archive edition.",
                       tokens_json="[]", sentiment_compound=.3, sentiment_label="positive",
                       published_at=now, retrieved_at=now),
        SocialDocument(source_name="Syndicated Feed", source_url="https://syndicated.example.com/song",
                       title="Blue Monday returns", summary="New Order announce an archive edition.",
                       tokens_json="[]", sentiment_compound=.3, sentiment_label="positive",
                       published_at=now, retrieved_at=now),
        SocialDocument(source_name="Example News", source_url="https://example.com/genre",
                       title="Electronic music update", summary="Electronic artists appear at a festival.",
                       tokens_json="[]", sentiment_compound=0, sentiment_label="neutral",
                       published_at=now, retrieved_at=now),
        SocialDocument(source_name="Example News", source_url="https://example.com/unrelated",
                       title="The will also first two", summary="An unrelated story.",
                       tokens_json="[]", sentiment_compound=0, sentiment_label="neutral",
                       published_at=now, retrieved_at=now),
    ])
    test_db.commit()

    result = TwsmaService.get_context_articles(test_db, artist="New Order", title="Blue Monday", genre="electronic")
    empty = TwsmaService.get_context_articles(test_db, artist="Nobody", title="Missing Song")

    assert result["status"] == "ok"
    assert sum(article["title"] == "Blue Monday returns" for article in result["articles"]) == 1
    assert result["articles"][0]["source_url"] == "https://example.com/song"
    assert {item["type"] for item in result["articles"][0]["matched_entities"]} == {"track", "artist"}
    assert result["social_posts"]["status"] == "unavailable"
    assert empty["status"] == "empty" and empty["articles"] == []
    tokens = TwsmaService.tokenize("The band will also play two new songs first")
    assert not ({"will", "also", "two", "first"} & set(tokens))


def test_seeded_recommendation_route(client, test_db, monkeypatch):
    add_track(test_db, "route-seed", "A New Song", "The Artist", ["pop"])
    monkeypatch.setattr(AppleCatalogueService, "search_related", classmethod(
        lambda cls, *args, **kwargs: {"status": "empty", "error": None, "retrieved_at": None, "tracks": []}
    ))
    response = client.post("/api/recommendations/seeded", json={
        "seed_title": "A New Song", "seed_artist": "The Artist", "limit": 10
    })
    assert response.status_code == 200
    assert response.json()["seed"]["title"] == "A New Song"
    assert response.json()["apple_status"] == "empty"


def test_apple_catalogue_search_route_is_available(client, monkeypatch):
    monkeypatch.setattr(AppleCatalogueService, "search_related", classmethod(lambda cls, *args, **kwargs: {
        "status": "ok", "error": None, "retrieved_at": None, "tracks": [{"id": "itunes-9", "title": "Result", "artist": "Artist"}]
    }))
    response = client.get("/api/music/apple-search?q=Result&limit=10")
    assert response.status_code == 200
    assert response.json()["tracks"][0]["id"] == "itunes-9"


def test_twsma_context_route_returns_truthful_empty_state(client):
    response = client.get("/api/twsma/context?artist=No%20Matching%20Artist&title=No%20Matching%20Song")
    assert response.status_code == 200
    assert response.json()["status"] == "empty"
    assert response.json()["social_posts"]["status"] == "unavailable"


def test_hybrid_weights_renormalize_across_real_available_signals(test_db, monkeypatch):
    seed = add_track(test_db, "seed", "Northern Lights", "The Band", ["indie"])
    candidate = add_track(test_db, "candidate", "Northern Road", "The Band", ["indie"], provider="lastfm", source="Last.fm tag chart")
    candidate.chart_rank = 4
    user = test_db.query(DemoUser).first()
    test_db.add_all([
        Interaction(user_id=user.id, track_id=seed.id, interaction_type="like", weight=1, is_synthetic_seed=False),
        Interaction(user_id=user.id, track_id=candidate.id, interaction_type="play", weight=.5, is_synthetic_seed=False),
        SocialDocument(source_name="Music News", source_url="https://example.com/north", title="The Band tour news",
                       summary="The Band discuss their indie album.", tokens_json="[]", sentiment_compound=.1,
                       sentiment_label="positive", published_at=datetime.now(timezone.utc), retrieved_at=datetime.now(timezone.utc)),
    ])
    test_db.commit()
    monkeypatch.setattr(AppleCatalogueService, "search_related", classmethod(lambda cls, *args, **kwargs: {
        "status": "empty", "error": None, "retrieved_at": None, "tracks": []
    }))

    result = SeedRecommendationService.generate(test_db, title=seed.title, artist=seed.artist, genre="indie")
    ranked = next(item for item in result["tracks"] if item["id"] == candidate.id)
    assert ranked["components"]["content"]["available"]
    assert ranked["components"]["collaborative"]["available"]
    assert ranked["components"]["trend"]["available"]
    assert ranked["components"]["news"]["available"]
    assert sum(ranked["effective_weights"].values()) == pytest.approx(1.0)
    assert set(ranked["effective_weights"]) == {"content", "collaborative", "trend", "news"}


def test_missing_lastfm_data_does_not_invent_trend_score(test_db, monkeypatch):
    seed = add_track(test_db, "seed", "Reference Song", "Reference Artist", ["jazz"])
    candidate = add_track(test_db, "candidate", "Related Song", "Reference Artist", ["jazz"])
    candidate.chart_rank = 1
    candidate.listener_count = 999999
    test_db.commit()
    monkeypatch.setattr(AppleCatalogueService, "search_related", classmethod(lambda cls, *args, **kwargs: {
        "status": "empty", "error": None, "retrieved_at": None, "tracks": []
    }))

    result = SeedRecommendationService.generate(test_db, title=seed.title, artist=seed.artist)

    ranked = next(item for item in result["tracks"] if item["id"] == candidate.id)
    assert ranked["components"]["trend"]["available"] is False
    assert ranked["components"]["trend"]["score"] is None
    assert ranked["effective_weights"] == {"content": 1.0}


def test_apple_api_normalizes_trusted_links_and_rejects_untrusted_links(monkeypatch):
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"results": [
                {"trackId": 7, "trackName": "Verified Track", "artistName": "Verified Artist",
                 "previewUrl": "http://audio-ssl.itunes.apple.com/preview.m4a",
                 "trackViewUrl": "https://music.apple.com/song/7",
                 "artworkUrl100": "http://is1-ssl.mzstatic.com/artwork.jpg"},
                {"trackId": 8, "trackName": "Bad Preview", "artistName": "Verified Artist",
                 "previewUrl": "https://example.org/stranger.mp3",
                 "trackViewUrl": "https://example.org/item/8",
                 "artworkUrl100": "https://example.org/image.jpg"},
            ]}
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url, params): return Response()
    import backend.app.services.apple_catalogue_service as apple_module
    monkeypatch.setattr(apple_module.httpx, "Client", Client)

    result = AppleCatalogueService.search_related("Verified Track", "Verified Artist")

    assert result["status"] == "ok"
    assert result["tracks"][0]["preview_url"] == "https://audio-ssl.itunes.apple.com/preview.m4a"
    assert result["tracks"][0]["store_url"] == "https://music.apple.com/song/7"
    assert result["tracks"][1]["preview_url"] is None
    assert result["tracks"][1]["store_url"] is None
    assert result["tracks"][1]["image_url"] is None


def test_twsma_sync_supports_multiple_configured_rss_feeds(test_db, monkeypatch):
    monkeypatch.setattr(settings, "MUSIC_RSS_FEEDS", "https://one.example/rss,https://two.example/rss")
    requested = []
    class Response:
        status_code = 200
        content = b"<rss><channel><item><title>Artist announces tour</title><link>https://news.example/story</link><description>Music news</description></item></channel></rss>"
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def get(self, url, headers):
            requested.append(url)
            # Keep URLs distinct so URL-level deduplication retains one item per feed.
            self_response = Response()
            self_response.content = f"<rss><channel><item><title>Artist announces tour</title><link>{url}/story</link><description>Music news</description></item></channel></rss>".encode()
            return self_response
    import backend.app.services.twsma_service as twsma_module
    monkeypatch.setattr(twsma_module.httpx, "Client", Client)

    result = TwsmaService.sync_news_feed(test_db)

    assert requested == ["https://one.example/rss", "https://two.example/rss"]
    assert result["articles_added"] == 2
    assert test_db.query(SocialDocument).count() == 2
