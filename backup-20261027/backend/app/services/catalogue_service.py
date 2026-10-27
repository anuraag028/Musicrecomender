import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from backend.app.models import Track, Release, DemoUser, Interaction, ApiCache
from backend.app.services.musicbrainz_service import MusicBrainzService
from backend.app.services.lastfm_service import LastFmService
from backend.app.services.youtube_service import YouTubeService
from backend.app.logging_config import record_log

INITIAL_DEMO_USERS = [
    {
        "id": "demo-user-1",
        "name": "Alex Vance",
        "label": "SYNTHETIC / DEMO PROFILE",
        "bio": "Indie Rock, Post-Punk & Shoegaze enthusiast. Enjoys deep cuts, gritty guitars, and atmospheric textures.",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
        "preferred_genres": ["indie rock", "alternative rock", "shoegaze", "post-punk", "grunge"]
    },
    {
        "id": "demo-user-2",
        "name": "Beatrix Chen",
        "label": "SYNTHETIC / DEMO PROFILE",
        "bio": "Pop, Dance & Electropop follower. Consumes chart-topping rhythms, upbeat hooks, and high-energy club anthems.",
        "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80",
        "preferred_genres": ["pop", "dance", "electropop", "disco", "r&b"]
    },
    {
        "id": "demo-user-3",
        "name": "Charlie Miller",
        "label": "SYNTHETIC / DEMO PROFILE",
        "bio": "Electronic, Synthwave & Ambient soundscape explorer. Focuses on melodic synthesizers and progressive BPM.",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
        "preferred_genres": ["electronic", "synthwave", "ambient", "techno", "downtempo"]
    }
]

class CatalogueService:
    @staticmethod
    def ensure_demo_users(db: Session):
        """Ensures the 3 synthetic demo profiles exist in database."""
        for u in INITIAL_DEMO_USERS:
            existing = db.query(DemoUser).filter(DemoUser.id == u["id"]).first()
            if not existing:
                demo_user = DemoUser(
                    id=u["id"],
                    name=u["name"],
                    label=u["label"],
                    bio=u["bio"],
                    avatar=u["avatar"],
                    preferred_genres=json.dumps(u["preferred_genres"]),
                    created_at=datetime.now(timezone.utc)
                )
                db.add(demo_user)
        db.commit()

    @staticmethod
    def normalize_string(s: str) -> str:
        return " ".join(s.strip().lower().split())

    @classmethod
    def ingest_musicbrainz_recording(cls, db: Session, rec: Dict[str, Any], is_trending: bool = False, rank: Optional[int] = None) -> Optional[Track]:
        mbid = rec.get("id")
        title = rec.get("title")
        if not mbid or not title:
            return None

        # Extract artist
        artist_credits = rec.get("artist-credit", [])
        if artist_credits and isinstance(artist_credits, list):
            artist_name = "".join(ac.get("name", "") + ac.get("joinphrase", "") for ac in artist_credits if isinstance(ac, dict))
        else:
            artist_name = "Unknown Artist"

        # Check existing by MBID or (artist, title)
        norm_artist = cls.normalize_string(artist_name)
        norm_title = cls.normalize_string(title)

        existing = (
            db.query(Track)
            .filter(
                or_(
                    Track.provider_id == mbid,
                    (func.lower(Track.artist) == norm_artist) & (func.lower(Track.title) == norm_title)
                )
            )
            .first()
        )

        # Extract genres/tags
        tag_list = []
        for t in rec.get("tags", []):
            if isinstance(t, dict) and t.get("name"):
                tag_list.append(t.get("name").lower())

        # Extract release info
        releases = rec.get("releases", [])
        album_name = None
        release_date = None
        if releases and isinstance(releases, list):
            album_name = releases[0].get("title")
            release_date = releases[0].get("date")

        length_ms = rec.get("length")

        # Resolve playback embed reference
        playback_info = YouTubeService.resolve_video(db, artist_name, title)

        if existing:
            # Update trending status if newly marked
            if is_trending:
                existing.is_trending = True
                existing.chart_rank = rank
            if tag_list and not json.loads(existing.tags or "[]"):
                existing.tags = json.dumps(tag_list)
            if not existing.playback_id and playback_info.get("playback_id"):
                existing.playback_id = playback_info.get("playback_id")
                existing.playback_verified = playback_info.get("playback_verified", False)
            db.commit()
            return existing

        track_id = f"mb-{mbid}"
        new_track = Track(
            id=track_id,
            provider="musicbrainz",
            provider_id=mbid,
            title=title,
            artist=artist_name,
            album=album_name,
            release_date=release_date,
            genres=json.dumps(tag_list[:3]),
            tags=json.dumps(tag_list),
            duration_ms=length_ms,
            image_url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&auto=format&fit=crop&q=80",
            playback_provider=playback_info.get("playback_provider", "youtube"),
            playback_id=playback_info.get("playback_id"),
            playback_verified=playback_info.get("playback_verified", False),
            is_trending=is_trending,
            chart_rank=rank,
            provenance_source="MusicBrainz Web Service (WS/2)",
            raw_metadata_json=json.dumps(rec),
            fetched_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(new_track)
        db.commit()
        return new_track

    @classmethod
    def ingest_lastfm_track(cls, db: Session, item: Dict[str, Any], rank: int) -> Optional[Track]:
        title = item.get("name")
        artist_obj = item.get("artist")
        artist_name = artist_obj.get("name") if isinstance(artist_obj, dict) else str(artist_obj or "")
        mbid = item.get("mbid") or f"lfm-{hash(f'{artist_name}-{title}')}"

        if not title or not artist_name:
            return None

        norm_artist = cls.normalize_string(artist_name)
        norm_title = cls.normalize_string(title)

        existing = (
            db.query(Track)
            .filter(
                or_(
                    Track.provider_id == mbid,
                    (func.lower(Track.artist) == norm_artist) & (func.lower(Track.title) == norm_title)
                )
            )
            .first()
        )

        play_count = int(item.get("playcount", 0)) if item.get("playcount") else None
        listener_count = int(item.get("listeners", 0)) if item.get("listeners") else None

        # Artwork
        images = item.get("image", [])
        image_url = None
        if images and isinstance(images, list):
            for img in reversed(images):
                if isinstance(img, dict) and img.get("#text"):
                    image_url = img.get("#text")
                    break

        # Resolve playback
        playback_info = YouTubeService.resolve_video(db, artist_name, title)

        if existing:
            existing.is_trending = True
            existing.chart_rank = rank
            if play_count:
                existing.play_count = play_count
            if listener_count:
                existing.listener_count = listener_count
            if image_url:
                existing.image_url = image_url
            if not existing.playback_id and playback_info.get("playback_id"):
                existing.playback_id = playback_info.get("playback_id")
                existing.playback_verified = playback_info.get("playback_verified", False)
            db.commit()
            return existing

        track_id = f"lfm-{uuid.uuid4().hex[:12]}"
        new_track = Track(
            id=track_id,
            provider="lastfm",
            provider_id=mbid,
            title=title,
            artist=artist_name,
            play_count=play_count,
            listener_count=listener_count,
            image_url=image_url or "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&auto=format&fit=crop&q=80",
            playback_provider=playback_info.get("playback_provider", "youtube"),
            playback_id=playback_info.get("playback_id"),
            playback_verified=playback_info.get("playback_verified", False),
            is_trending=True,
            chart_rank=rank,
            provenance_source="Last.fm Chart API (chart.gettoptracks)",
            raw_metadata_json=json.dumps(item),
            fetched_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=3)
        )
        db.add(new_track)
        db.commit()
        return new_track

    @classmethod
    def sync_trending(cls, db: Session, limit: int = 20) -> List[Track]:
        """
        Synchronizes real trending tracks.
        First checks Last.fm. If unconfigured/unavailable, uses real MusicBrainz curated search.
        """
        tracks = []
        if LastFmService.is_configured():
            res = LastFmService.get_chart_top_tracks(db, limit=limit)
            raw_tracks = res.get("tracks", [])
            for idx, raw in enumerate(raw_tracks[:limit]):
                t = cls.ingest_lastfm_track(db, raw, rank=idx + 1)
                if t:
                    tracks.append(t)
            if tracks:
                return tracks

        # Fallback to MusicBrainz real recordings query
        record_log("INFO", "Syncing trending tracks via MusicBrainz search query")
        queries = ["tag:rock", "tag:pop", "tag:indie", "tag:electronic"]
        rank_counter = 1
        for q in queries:
            recs = MusicBrainzService.search_recordings(db, query=f"{q} AND date:[2023-01-01 TO 2026-12-31]", limit=5)
            for r in recs:
                t = cls.ingest_musicbrainz_recording(db, r, is_trending=True, rank=rank_counter)
                if t:
                    tracks.append(t)
                    rank_counter += 1
                if len(tracks) >= limit:
                    break
            if len(tracks) >= limit:
                break

        return tracks

    @classmethod
    def sync_new_releases(cls, db: Session, limit: int = 15) -> List[Release]:
        """Syncs genuine recent releases from MusicBrainz."""
        raw_releases = MusicBrainzService.get_new_releases(db, limit=limit)
        results = []
        for r in raw_releases:
            rel_id = r.get("id")
            title = r.get("title")
            if not rel_id or not title:
                continue

            artist_credit = r.get("artist-credit", [])
            artist_name = "".join(ac.get("name", "") + ac.get("joinphrase", "") for ac in artist_credit if isinstance(ac, dict)) if artist_credit else "Unknown Artist"

            existing = db.query(Release).filter(Release.id == f"mb-{rel_id}").first()
            if existing:
                results.append(existing)
                continue

            rel_date = r.get("date")
            status = r.get("status", "Official")
            new_rel = Release(
                id=f"mb-{rel_id}",
                title=title,
                artist=artist_name,
                release_date=rel_date,
                release_type=status,
                provider="musicbrainz",
                provider_id=rel_id,
                image_url="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&auto=format&fit=crop&q=80",
                provenance_source="MusicBrainz Release Catalog (WS/2)",
                fetched_at=datetime.now(timezone.utc)
            )
            db.add(new_rel)
            results.append(new_rel)

        db.commit()
        return results

    @classmethod
    def search_catalogue(cls, db: Session, query: str, limit: int = 20) -> List[Track]:
        """Searches local database; if sparse, executes real MusicBrainz query and ingests."""
        q_norm = f"%{query.strip().lower()}%"
        local_matches = (
            db.query(Track)
            .filter(
                or_(
                    func.lower(Track.title).like(q_norm),
                    func.lower(Track.artist).like(q_norm),
                    func.lower(Track.genres).like(q_norm),
                    func.lower(Track.tags).like(q_norm)
                )
            )
            .limit(limit)
            .all()
        )

        if len(local_matches) >= 5:
            return local_matches

        # Query live MusicBrainz for additional genuine tracks
        record_log("INFO", f"Live searching MusicBrainz for '{query}'")
        mb_recordings = MusicBrainzService.search_recordings(db, query=query, limit=10)
        for r in mb_recordings:
            cls.ingest_musicbrainz_recording(db, r)

        # Re-query local database
        return (
            db.query(Track)
            .filter(
                or_(
                    func.lower(Track.title).like(q_norm),
                    func.lower(Track.artist).like(q_norm),
                    func.lower(Track.genres).like(q_norm),
                    func.lower(Track.tags).like(q_norm)
                )
            )
            .limit(limit)
            .all()
        )

    @classmethod
    def seed_synthetic_interactions_if_empty(cls, db: Session):
        """
        Seeds initial synthetic interactions for the 3 demo users ONLY over real catalogue tracks
        present in database.
        Clearly labels all seeded rows with `is_synthetic_seed = True`.
        """
        interaction_count = db.query(Interaction).count()
        if interaction_count > 0:
            return

        tracks = db.query(Track).all()
        if not tracks:
            # Honest state: No fake tracks are ever invented.
            return

        # Distribute interactions according to demo profile preferences
        # Limit to 3 initial seed interactions per demo profile so other tracks remain available candidates
        user_1_count = 0
        user_2_count = 0
        user_3_count = 0

        for idx, t in enumerate(tracks):
            tags_str = (t.tags or "").lower() + " " + (t.genres or "").lower() + " " + t.artist.lower()

            # User 1 (Alex - Indie / Rock)
            if user_1_count < 3 and any(k in tags_str for k in ["rock", "indie", "alternative", "post-punk", "grunge"]):
                db.add(Interaction(
                    user_id="demo-user-1",
                    track_id=t.id,
                    interaction_type="like",
                    weight=1.0,
                    is_synthetic_seed=True,
                    created_at=datetime.now(timezone.utc)
                ))
                user_1_count += 1
            elif user_1_count < 3 and idx % 4 == 0:
                db.add(Interaction(
                    user_id="demo-user-1",
                    track_id=t.id,
                    interaction_type="skip",
                    weight=-0.5,
                    is_synthetic_seed=True,
                    created_at=datetime.now(timezone.utc)
                ))
                user_1_count += 1

            # User 2 (Beatrix - Pop / Dance)
            if user_2_count < 3 and any(k in tags_str for k in ["pop", "dance", "disco", "r&b", "electropop"]):
                db.add(Interaction(
                    user_id="demo-user-2",
                    track_id=t.id,
                    interaction_type="like",
                    weight=1.0,
                    is_synthetic_seed=True,
                    created_at=datetime.now(timezone.utc)
                ))
                user_2_count += 1
            elif user_2_count < 3 and idx % 3 == 0:
                db.add(Interaction(
                    user_id="demo-user-2",
                    track_id=t.id,
                    interaction_type="play",
                    weight=0.5,
                    is_synthetic_seed=True,
                    created_at=datetime.now(timezone.utc)
                ))
                user_2_count += 1

            # User 3 (Charlie - Electronic / Synth)
            if user_3_count < 3 and any(k in tags_str for k in ["electronic", "synth", "ambient", "techno", "downtempo"]):
                db.add(Interaction(
                    user_id="demo-user-3",
                    track_id=t.id,
                    interaction_type="like",
                    weight=1.0,
                    is_synthetic_seed=True,
                    created_at=datetime.now(timezone.utc)
                ))
                user_3_count += 1

        db.commit()
        record_log("INFO", f"Seeded synthetic interactions for demo users over {len(tracks)} real catalogue tracks")
