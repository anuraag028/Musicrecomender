import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Track, DemoUser, Interaction, RecommendationRun, RecommendationItem
from backend.app.services.twsma_service import TwsmaService
from backend.app.logging_config import record_log

class RecommendationEngine:
    @staticmethod
    def _compute_content_scores(
        user: DemoUser,
        user_interactions: List[Interaction],
        candidate_tracks: List[Track]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates content-based similarity [0.0, 1.0] between user preference profile
        and candidate tracks using TF-IDF on genre, tags, and artist.
        """
        results = {}
        if not candidate_tracks:
            return results

        # Construct user preference profile text
        preferred_genres = json.loads(user.preferred_genres or "[]")
        user_text_parts = preferred_genres.copy()

        # Add genres/tags from positively interacted tracks
        positive_tracks = [
            i.track for i in user_interactions
            if i.weight > 0 and i.track is not None
        ]
        for pt in positive_tracks:
            tags = json.loads(pt.tags or "[]")
            genres = json.loads(pt.genres or "[]")
            user_text_parts.extend(tags)
            user_text_parts.extend(genres)
            user_text_parts.append(pt.artist)

        user_profile_text = " ".join(user_text_parts).strip()
        if not user_profile_text:
            # Fallback when profile is completely empty
            for t in candidate_tracks:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": "User profile has no explicit genre preferences or positive interaction history.",
                    "evidence": []
                }
            return results

        # Build corpus: index 0 is user profile, remaining are candidates
        corpus = [user_profile_text]
        track_tokens = []
        for t in candidate_tracks:
            tags = json.loads(t.tags or "[]")
            genres = json.loads(t.genres or "[]")
            t_text = f"{t.artist} {' '.join(genres)} {' '.join(tags)}"
            corpus.append(t_text)
            track_tokens.append(set(tags + genres + [t.artist.lower()]))

        try:
            vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            tfidf_matrix = vectorizer.fit_transform(corpus)
            user_vec = tfidf_matrix[0:1]
            candidate_vecs = tfidf_matrix[1:]
            sims = cosine_similarity(user_vec, candidate_vecs)[0]

            for idx, t in enumerate(candidate_tracks):
                sim_score = float(sims[idx])
                # Find matching tokens
                matching_terms = [
                    w for w in preferred_genres
                    if w.lower() in track_tokens[idx] or any(w.lower() in tok for tok in track_tokens[idx])
                ]
                bounded_score = round(max(0.0, min(1.0, sim_score)), 4)
                results[t.id] = {
                    "available": True,
                    "score": bounded_score,
                    "reason": f"Content match based on shared attributes: {', '.join(matching_terms) if matching_terms else 'genre vector alignment'}",
                    "evidence": [{"matching_terms": matching_terms, "raw_cosine_similarity": round(sim_score, 4)}]
                }
        except Exception as e:
            record_log("ERROR", f"Content-based calculation error: {str(e)}")
            for t in candidate_tracks:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": f"Content vectorization error: {str(e)}",
                    "evidence": []
                }

        return results

    @staticmethod
    def _compute_collaborative_scores(
        db: Session,
        target_user_id: str,
        user_interactions: List[Interaction],
        candidate_tracks: List[Track]
    ) -> Dict[str, Dict[str, Any]]:
        """
        User-based Collaborative Filtering using interaction matrix.
        Cold-start users with zero interactions receive an honest unavailable/cold-start result.
        """
        results = {}
        if not user_interactions:
            # Explicit cold start
            for t in candidate_tracks:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": "Cold-start user: no prior listening history or ratings exist for this profile.",
                    "evidence": []
                }
            return results

        # Fetch all interactions in database
        all_interactions = db.query(Interaction).all()
        user_ids = sorted(list(set(i.user_id for i in all_interactions)))
        track_ids = sorted(list(set(i.track_id for i in all_interactions)))

        if len(user_ids) < 2 or not track_ids:
            for t in candidate_tracks:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": "Insufficient community interaction density to calculate collaborative similarity.",
                    "evidence": []
                }
            return results

        user_idx_map = {uid: idx for idx, uid in enumerate(user_ids)}
        track_idx_map = {tid: idx for idx, tid in enumerate(track_ids)}

        # Build user-item interaction matrix
        R = np.zeros((len(user_ids), len(track_ids)), dtype=float)
        for i in all_interactions:
            u_idx = user_idx_map.get(i.user_id)
            t_idx = track_idx_map.get(i.track_id)
            if u_idx is not None and t_idx is not None:
                R[u_idx, t_idx] = i.weight

        target_u_idx = user_idx_map.get(target_user_id)
        if target_u_idx is None or np.linalg.norm(R[target_u_idx]) == 0:
            for t in candidate_tracks:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": "Cold-start target user profile in interaction matrix.",
                    "evidence": []
                }
            return results

        # Compute cosine similarity between target user and other users
        user_sims = cosine_similarity(R[target_u_idx:target_u_idx+1], R)[0]

        for t in candidate_tracks:
            t_col = track_idx_map.get(t.id)
            if t_col is None:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": "Track has no community interactions yet.",
                    "evidence": []
                }
                continue

            # Predict rating using weighted sum over other users
            sim_sum = 0.0
            weighted_rating_sum = 0.0
            similar_users_evidence = []

            for other_u_id, other_u_idx in user_idx_map.items():
                if other_u_id == target_user_id:
                    continue
                sim = user_sims[other_u_idx]
                r = R[other_u_idx, t_col]
                if r != 0 and sim > 0:
                    weighted_rating_sum += sim * r
                    sim_sum += sim
                    similar_users_evidence.append({
                        "user_id": other_u_id,
                        "similarity": round(float(sim), 3),
                        "interaction_weight": r
                    })

            if sim_sum > 0:
                raw_pred = weighted_rating_sum / sim_sum
                # Normalize raw_pred (which can range from -1.0 to 1.0) into [0.0, 1.0]
                norm_score = (raw_pred + 1.0) / 2.0
                bounded_score = round(max(0.0, min(1.0, norm_score)), 4)
                results[t.id] = {
                    "available": True,
                    "score": bounded_score,
                    "reason": f"Collaborative signal from {len(similar_users_evidence)} peer user profile(s).",
                    "evidence": similar_users_evidence[:3]
                }
            else:
                results[t.id] = {
                    "available": False,
                    "score": None,
                    "reason": "No similar peer users have interacted with this track.",
                    "evidence": []
                }

        return results

    @staticmethod
    def _compute_trend_scores(candidate_tracks: List[Track]) -> Dict[str, Dict[str, Any]]:
        """
        Derives normalized trend score [0.0, 1.0] from real chart ranks, playcounts, or listener metrics.
        """
        results = {}
        if not candidate_tracks:
            return results

        # Find maximum playcount/listener count for normalization
        max_listeners = max([t.listener_count or 0 for t in candidate_tracks] + [1])

        for t in candidate_tracks:
            if t.chart_rank:
                # Rank 1 is top trend (score = 1.0), rank 50 is 0.5, etc.
                rank_score = max(0.2, 1.0 - (t.chart_rank - 1) * 0.02)
                results[t.id] = {
                    "available": True,
                    "score": round(rank_score, 4),
                    "reason": f"Chart position #{t.chart_rank} from {t.provenance_source}",
                    "evidence": [{"chart_rank": t.chart_rank, "provenance": t.provenance_source}]
                }
            elif t.listener_count and t.listener_count > 0:
                listener_norm = min(1.0, t.listener_count / max_listeners)
                results[t.id] = {
                    "available": True,
                    "score": round(max(0.1, listener_norm), 4),
                    "reason": f"Verified listener count: {t.listener_count:,} from {t.provenance_source}",
                    "evidence": [{"listener_count": t.listener_count, "provenance": t.provenance_source}]
                }
            elif t.is_trending:
                results[t.id] = {
                    "available": True,
                    "score": 0.65,
                    "reason": f"Featured trending track from {t.provenance_source}",
                    "evidence": [{"is_trending": True, "provenance": t.provenance_source}]
                }
            else:
                results[t.id] = {
                    "available": True,
                    "score": 0.10,
                    "reason": "Standard catalogue track without global chart positioning",
                    "evidence": [{"baseline_trend": 0.10}]
                }

        return results

    @staticmethod
    def _compute_text_scores(db: Session, candidate_tracks: List[Track]) -> Dict[str, Dict[str, Any]]:
        """
        Computes real text/social signal from TwsmaService based on genuine news RSS articles.
        """
        results = {}
        for t in candidate_tracks:
            res = TwsmaService.calculate_text_signal_for_artist(db, t.artist, t.title)
            results[t.id] = res
        return results

    @classmethod
    def generate_recommendations(
        cls,
        db: Session,
        user_id: str,
        limit: int = 10,
        diversity_penalty: float = 0.15,
        exclude_played: bool = True,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Tuple[RecommendationRun, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes complete hybrid recommendation pipeline, records run trace, and returns
        reproducible numeric explainability output.
        """
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        user = db.query(DemoUser).filter(DemoUser.id == user_id).first()
        if not user:
            raise ValueError(f"Demo user '{user_id}' does not exist.")

        # Default configured weights
        configured_weights = {
            "content": settings.WEIGHT_CONTENT,
            "collaborative": settings.WEIGHT_COLLABORATIVE,
            "trend": settings.WEIGHT_TREND,
            "text": settings.WEIGHT_TEXT,
        }
        if custom_weights:
            configured_weights.update(custom_weights)

        # 1. Candidate Retrieval
        all_tracks = db.query(Track).all()
        retrieved_count = len(all_tracks)

        # 2. Deduplication check
        dedup_dict = {}
        for t in all_tracks:
            key = f"{t.artist.lower().strip()}||{t.title.lower().strip()}"
            if key not in dedup_dict:
                dedup_dict[key] = t
        deduplicated_tracks = list(dedup_dict.values())
        deduplicated_count = len(deduplicated_tracks)

        # Fetch user interactions
        user_interactions = db.query(Interaction).filter(Interaction.user_id == user_id).all()
        played_track_ids = {i.track_id for i in user_interactions if i.interaction_type in ["play", "like", "rate"]}
        disliked_track_ids = {i.track_id for i in user_interactions if i.interaction_type in ["dislike", "skip"] and i.weight < 0}

        # Filtering / Funnel
        excluded_played_count = 0
        excluded_disliked_count = 0
        excluded_playback_count = 0
        filtered_candidates: List[Track] = []
        exclusions_trace = []

        for t in deduplicated_tracks:
            if exclude_played and t.id in played_track_ids:
                excluded_played_count += 1
                exclusions_trace.append({"track_id": t.id, "title": t.title, "artist": t.artist, "reason": "Already played/liked by selected user"})
                continue
            if t.id in disliked_track_ids:
                excluded_disliked_count += 1
                exclusions_trace.append({"track_id": t.id, "title": t.title, "artist": t.artist, "reason": "Skipped/disliked in previous session"})
                continue
            # If no playback reference at all
            if not t.playback_id and not t.playback_provider:
                excluded_playback_count += 1
                exclusions_trace.append({"track_id": t.id, "title": t.title, "artist": t.artist, "reason": "No playable audio/video provider available"})
                continue

            filtered_candidates.append(t)

        playback_eligible_count = len(filtered_candidates)
        scored_count = len(filtered_candidates)

        # 3. Calculate component scores
        content_res = cls._compute_content_scores(user, user_interactions, filtered_candidates)
        collab_res = cls._compute_collaborative_scores(db, user_id, user_interactions, filtered_candidates)
        trend_res = cls._compute_trend_scores(filtered_candidates)
        text_res = cls._compute_text_scores(db, filtered_candidates)

        # 4. Hybrid Scoring with Dynamic Weight Renormalization
        scored_tracks = []
        for t in filtered_candidates:
            c_info = content_res.get(t.id, {"available": False, "score": None, "reason": "No content info"})
            cb_info = collab_res.get(t.id, {"available": False, "score": None, "reason": "No collaborative info"})
            tr_info = trend_res.get(t.id, {"available": False, "score": None, "reason": "No trend info"})
            tx_info = text_res.get(t.id, {"available": False, "score": None, "reason": "No text info"})

            components_map = {
                "content": c_info,
                "collaborative": cb_info,
                "trend": tr_info,
                "text": tx_info
            }

            # Renormalize active weights
            available_components = {k: v for k, v in components_map.items() if v.get("available") and v.get("score") is not None}
            sum_available_weight = sum(configured_weights[k] for k in available_components.keys())

            effective_weights = {}
            if sum_available_weight > 0:
                for k in available_components.keys():
                    effective_weights[k] = round(configured_weights[k] / sum_available_weight, 4)
            else:
                # Ultimate fallback if nothing available: trend fallback
                effective_weights = {"trend": 1.0}
                tr_info["available"] = True
                tr_info["score"] = 0.5
                available_components["trend"] = tr_info

            # Compute weighted contributions
            final_score = 0.0
            reasons = []
            component_evidence_dict = {}

            for comp_name in ["content", "collaborative", "trend", "text"]:
                info = components_map[comp_name]
                if comp_name in available_components:
                    sc = info["score"]
                    eff_w = effective_weights[comp_name]
                    contrib = round(sc * eff_w, 4)
                    final_score += contrib
                    component_evidence_dict[comp_name] = {
                        "available": True,
                        "score": sc,
                        "weighted_contribution": contrib,
                        "reason": info.get("reason"),
                        "evidence": info.get("evidence", [])
                    }
                    if info.get("reason"):
                        reasons.append(f"[{comp_name.capitalize()}] {info['reason']}")
                else:
                    component_evidence_dict[comp_name] = {
                        "available": False,
                        "score": None,
                        "weighted_contribution": 0.0,
                        "reason": info.get("reason", "Signal unavailable"),
                        "evidence": []
                    }

            final_score = round(min(1.0, max(0.0, final_score)), 4)

            scored_tracks.append({
                "track": t,
                "final_score": final_score,
                "effective_weights": effective_weights,
                "components": component_evidence_dict,
                "reasons": reasons,
                "data_sources": [t.provenance_source]
            })

        # 5. Ranking and Diversity Filter
        # Sort descending by raw hybrid score
        scored_tracks.sort(key=lambda x: x["final_score"], reverse=True)

        ranked_tracks = []
        artist_counts = {}
        for item in scored_tracks:
            t = item["track"]
            # Apply diversity penalty if artist was already recently queued
            art = t.artist.lower()
            current_art_count = artist_counts.get(art, 0)
            penalty = current_art_count * diversity_penalty
            adjusted_score = round(max(0.0, item["final_score"] - penalty), 4)

            item["adjusted_score"] = adjusted_score
            ranked_tracks.append(item)
            artist_counts[art] = current_art_count + 1

        # Re-sort with diversity adjustments
        ranked_tracks.sort(key=lambda x: x["adjusted_score"], reverse=True)
        selected_tracks = ranked_tracks[:limit]
        selected_count = len(selected_tracks)

        # Candidate Funnel
        funnel = {
            "retrieved": retrieved_count,
            "deduplicated": deduplicated_count,
            "excluded_already_played": excluded_played_count,
            "excluded_disliked": excluded_disliked_count,
            "excluded_unavailable_playback": excluded_playback_count,
            "playback_eligible": playback_eligible_count,
            "scored": scored_count,
            "selected": selected_count
        }

        # Format output items with rank
        output_items = []
        for idx, item in enumerate(selected_tracks):
            t = item["track"]
            output_items.append({
                "rank": idx + 1,
                "track_id": t.id,
                "title": t.title,
                "artist": t.artist,
                "album": t.album,
                "image_url": t.image_url,
                "playback_id": t.playback_id,
                "playback_verified": t.playback_verified,
                "final_score": item["final_score"],
                "components": item["components"],
                "reasons": item["reasons"],
                "data_sources": item["data_sources"]
            })

        # Generate representative effective weights for trace
        avg_effective_weights = {}
        if selected_tracks:
            sample_weights = selected_tracks[0]["effective_weights"]
            avg_effective_weights = sample_weights
        else:
            avg_effective_weights = configured_weights

        trace_payload = {
            "run_id": run_id,
            "user_id": user_id,
            "data_mode": "live_with_synthetic_demo_interactions",
            "generated_at": now_iso,
            "formula": "hybrid = sum(effective_weight * available_component_score)",
            "configured_weights": configured_weights,
            "effective_weights": avg_effective_weights,
            "candidate_funnel": funnel,
            "ranked_tracks": output_items,
            "exclusions": exclusions_trace[:10]
        }

        # Persist RecommendationRun to database
        db_run = RecommendationRun(
            run_id=run_id,
            user_id=user_id,
            data_mode="live_with_synthetic_demo_interactions",
            configured_weights_json=json.dumps(configured_weights),
            effective_weights_json=json.dumps(avg_effective_weights),
            candidate_funnel_json=json.dumps(funnel),
            trace_json=json.dumps(trace_payload),
            created_at=datetime.now(timezone.utc)
        )
        db.add(db_run)

        # Persist RecommendationItems
        for itm in output_items:
            db_item = RecommendationItem(
                run_id=run_id,
                track_id=itm["track_id"],
                rank=itm["rank"],
                content_score=itm["components"]["content"]["score"] or 0.0,
                collaborative_score=itm["components"]["collaborative"]["score"] or 0.0,
                trend_score=itm["components"]["trend"]["score"] or 0.0,
                text_score=itm["components"]["text"]["score"],
                final_score=itm["final_score"],
                reasons_json=json.dumps(itm["reasons"]),
                is_playback_eligible=True
            )
            db.add(db_item)

        db.commit()

        record_log(
            "INFO",
            f"Recommendation run {run_id} completed for user {user_id}",
            run_id=run_id,
            details={"funnel": funnel, "effective_weights": avg_effective_weights}
        )

        return db_run, output_items, funnel
