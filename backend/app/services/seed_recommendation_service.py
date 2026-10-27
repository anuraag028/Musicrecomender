import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.config import settings
from backend.app.models import Interaction, SocialDocument, Track
from backend.app.services.apple_catalogue_service import AppleCatalogueService
from backend.app.services.recommendation_engine import RecommendationEngine
from backend.app.services.twsma_service import TwsmaService


def normalize(value: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").casefold()))


def track_key(artist: str | None, title: str | None) -> Tuple[str, str]:
    return normalize(artist), normalize(title)


def _json_list(value: str | None) -> List[str]:
    try:
        result = json.loads(value or "[]")
        return [str(item) for item in result] if isinstance(result, list) else []
    except (TypeError, ValueError):
        return []


def _track_text(track: Any) -> str:
    if isinstance(track, dict):
        values = (track.get("title"), track.get("artist"), track.get("album"), track.get("genre"))
    else:
        values = (track.title, track.artist, track.album or "", *_json_list(track.genres), *_json_list(track.tags))
    return " ".join(str(value) for value in values if value)


def _content_score(seed_text: str, candidate_text: str) -> float:
    if not seed_text.strip() or not candidate_text.strip():
        return 0.0
    try:
        vectors = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b", ngram_range=(1, 2)).fit_transform([seed_text, candidate_text])
        return round(float(cosine_similarity(vectors[0:1], vectors[1:2])[0][0]), 4)
    except ValueError:
        return 0.0


class SeedRecommendationService:
    """Consistent seed-first hybrid ranking shared by For You and the smart queue."""

    @staticmethod
    def _collaborative_scores(db: Session, seed_track: Track | None, candidates: List[Track]) -> Dict[str, Dict[str, Any]]:
        no_data = {candidate.id: {"available": False, "score": None, "reason": "No real, non-demo interaction evidence is available.", "evidence": []} for candidate in candidates}
        if seed_track is None:
            return no_data
        interactions = db.query(Interaction).filter(Interaction.is_synthetic_seed.is_(False)).all()
        seed_positive = [i for i in interactions if i.track_id == seed_track.id and i.weight > 0 and i.interaction_type in {"like", "play", "rate"}]
        seed_users = {i.user_id for i in seed_positive}
        if not seed_users:
            return no_data
        output: Dict[str, Dict[str, Any]] = {}
        for candidate in candidates:
            observations = [i for i in interactions if i.track_id == candidate.id and i.user_id in seed_users and i.interaction_type in {"like", "play", "rate", "dislike", "skip"}]
            if not observations:
                output[candidate.id] = {"available": False, "score": None, "reason": "No real co-listener interaction for this candidate.", "evidence": []}
                continue
            per_user: Dict[str, float] = {}
            for item in observations:
                per_user[item.user_id] = max(per_user.get(item.user_id, 0.0), item.weight)
            score = sum(max(0.0, value) for value in per_user.values()) / max(1, len(seed_users))
            output[candidate.id] = {
                "available": True,
                "score": round(min(1.0, max(0.0, score)), 4),
                "reason": f"{len(per_user)} real user(s) who engaged positively with the seed also interacted with this track.",
                "evidence": [{"seed_engaged_users": len(seed_users), "matching_candidate_users": len(per_user), "interaction_source": "non-synthetic interaction records"}],
            }
        return output

    @staticmethod
    def _news_score(db: Session, artist: str, title: str, album: str | None, genre: str | None, documents: List[SocialDocument]) -> Dict[str, Any]:
        result = TwsmaService.get_context_articles(db, artist=artist, title=title, album=album or "", genre=genre or "", limit=5, documents=documents)
        articles = result["articles"]
        if not articles:
            return {"available": False, "score": None, "reason": "No matching music-news article is available.", "evidence": []}
        relevance = sum(item["relevance_score"] for item in articles) / len(articles)
        return {"available": True, "score": round(relevance, 4), "reason": f"{len(articles)} stored music-news article(s) mention candidate entities; this is not popularity evidence.",
                "evidence": [{"title": item["title"], "source_url": item["source_url"], "published_at": item["published_at"], "relevance_score": item["relevance_score"], "sentiment_label": item["sentiment_label"]} for item in articles]}

    @classmethod
    def generate(cls, db: Session, *, title: str = "", artist: str = "", album: str = "", genre: str = "", limit: int = 10) -> Dict[str, Any]:
        title, artist, album, genre = title.strip(), artist.strip(), album.strip(), genre.strip()
        if not (title or artist or genre):
            raise ValueError("Provide a seed track title, artist, or genre.")
        seed_track = None
        if title and artist:
            seed_track = db.query(Track).filter(Track.title.ilike(title), Track.artist.ilike(artist)).first()
        seed_text = " ".join(v for v in (title, artist, album, genre) if v)

        raw_db_tracks = db.query(Track).order_by(Track.title, Track.artist, Track.id).all()
        retrieved_count = len(raw_db_tracks)
        deduped: Dict[Tuple[str, str], Track] = {}
        for item in raw_db_tracks:
            deduped.setdefault(track_key(item.artist, item.title), item)
        db_candidates = list(deduped.values())
        seed_key = track_key(artist, title)
        db_candidates = [item for item in db_candidates if track_key(item.artist, item.title) != seed_key]

        collab = cls._collaborative_scores(db, seed_track, db_candidates)
        trend = RecommendationEngine._compute_trend_scores(db_candidates)
        article_docs = db.query(SocialDocument).order_by(SocialDocument.published_at.desc().nullslast(), SocialDocument.retrieved_at.desc()).limit(500).all()
        news = {t.id: cls._news_score(db, t.artist, t.title, t.album, ", ".join(_json_list(t.genres)), article_docs) for t in db_candidates}
        candidates: List[Dict[str, Any]] = []
        for item in db_candidates:
            content_score = _content_score(seed_text, _track_text(item))
            if content_score < 0.035:
                continue
            candidates.append({"record": item, "source": item.provenance_source, "content_score": content_score,
                               "collaborative": collab[item.id], "trend": trend[item.id], "news": news[item.id],
                               "provider_id": item.provider_id, "preview_url": None, "store_url": None,
                               "image_url": item.image_url, "retrieved_at": item.fetched_at.isoformat() if item.fetched_at else None})

        apple_response = AppleCatalogueService.search_related(title, artist, genre, limit=50)
        apple_added = 0
        apple_deduplicated = 0
        seen = {track_key(t.artist, t.title) for t in db_candidates}
        for item in apple_response.get("tracks", []):
            key = track_key(item.get("artist"), item.get("title"))
            if key in seen or key == seed_key:
                continue
            apple_deduplicated += 1
            score = _content_score(seed_text, _track_text(item))
            same_artist = bool(normalize(artist) and normalize(item.get("artist")) == normalize(artist))
            if score < 0.07 and not same_artist:
                continue
            seen.add(key)
            apple_added += 1
            candidates.append({"record": item, "source": "Apple iTunes", "content_score": max(score, 0.5 if same_artist else score),
                               "collaborative": {"available": False, "score": None, "reason": "Apple catalogue result has no local real-interaction history.", "evidence": []},
                               "trend": {"available": False, "score": None, "reason": "No verified Last.fm signal matched this Apple result.", "evidence": []},
                               "news": cls._news_score(db, item["artist"], item["title"], item.get("album"), item.get("genre"), article_docs),
                               "provider_id": item.get("provider_id"), "preview_url": item.get("preview_url"), "store_url": item.get("store_url"),
                               "image_url": item.get("image_url"), "retrieved_at": apple_response.get("retrieved_at")})

        configured = {
            "content": max(0.0, float(settings.WEIGHT_CONTENT)),
            "collaborative": max(0.0, float(settings.WEIGHT_COLLABORATIVE)),
            "trend": max(0.0, float(settings.WEIGHT_TREND)),
            "news": max(0.0, float(settings.WEIGHT_TEXT)),
        }
        ranked = []
        for candidate in candidates:
            components = {
                "content": {"available": True, "score": candidate["content_score"], "reason": "TF-IDF cosine similarity over seed and candidate metadata.", "evidence": ["title", "artist", "album", "genre", "tags"]},
                "collaborative": candidate["collaborative"], "trend": candidate["trend"], "news": candidate["news"],
            }
            available = {key: value for key, value in components.items() if value.get("available") and value.get("score") is not None and configured[key] > 0}
            total_weight = sum(configured[key] for key in available)
            if total_weight <= 0:
                continue
            effective = {key: round(configured[key] / total_weight, 6) for key in available}
            final_score = round(sum(float(components[key]["score"]) * effective[key] for key in available), 6)
            record = candidate["record"]
            is_db_track = isinstance(record, Track)
            ranked.append({
                "id": record.id if is_db_track else record["id"],
                "title": record.title if is_db_track else record["title"],
                "artist": record.artist if is_db_track else record["artist"],
                "album": record.album if is_db_track else record.get("album"),
                "genres": _json_list(record.genres) if is_db_track else ([record["genre"]] if record.get("genre") else []),
                "image_url": candidate["image_url"], "source": candidate["source"], "provider_id": candidate["provider_id"],
                "preview_url": candidate["preview_url"], "store_url": candidate["store_url"],
                "playback_availability": "preview" if candidate["preview_url"] and candidate["store_url"] else "metadata_only",
                "score": final_score,
                "components": {key: {**value, "weighted_contribution": round(float(value["score"]) * effective[key], 6) if key in effective else 0.0} for key, value in components.items()},
                "effective_weights": effective, "reasons": [value["reason"] for value in available.values()],
                "retrieved_at": candidate["retrieved_at"],
            })
        ranked.sort(key=lambda item: (-item["score"], normalize(item["artist"]), normalize(item["title"]), item["source"]))
        selected = ranked[:limit]
        apple_discoveries = [item for item in selected if item["source"] == "Apple iTunes"]
        effective_weights = selected[0]["effective_weights"] if selected else {}
        return {
            "seed": {"title": title or None, "artist": artist or None, "album": album or None, "genre": genre or None},
            "generated_at": datetime.now(timezone.utc).isoformat(), "count": len(selected), "tracks": selected,
            "apple_discoveries": apple_discoveries, "apple_status": apple_response.get("status"), "apple_error": apple_response.get("error"),
            "effective_weights": effective_weights,
            "funnel": {"retrieved": retrieved_count + len(apple_response.get("tracks", [])), "deduplicated": len(db_candidates) + apple_deduplicated, "filtered": len(ranked), "ranked": len(selected), "apple_relevant": apple_added},
            "methodology": "Per-candidate weighted sum over available signals; active weights are renormalized. Scores are ranking scores, not probabilities.",
            "collaborative_status": "Available from real interaction rows only." if seed_track and any(item.get("collaborative", {}).get("available") for item in candidates) else "Limited: no real, non-synthetic seed-linked interaction evidence.",
            "trend_status": "Verified Last.fm evidence included only where cached on a matching catalogue track.",
        }
