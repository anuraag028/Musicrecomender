import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Track(Base):
    __tablename__ = "tracks"

    id = Column(String(128), primary_key=True, index=True)
    provider = Column(String(32), nullable=False, index=True)  # 'musicbrainz', 'lastfm'
    provider_id = Column(String(128), nullable=False, index=True)
    title = Column(String(256), nullable=False, index=True)
    artist = Column(String(256), nullable=False, index=True)
    album = Column(String(256), nullable=True)
    release_date = Column(String(32), nullable=True)
    genres = Column(Text, default="[]")  # JSON string of list
    tags = Column(Text, default="[]")    # JSON string of list
    play_count = Column(Integer, nullable=True)
    listener_count = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    image_url = Column(Text, nullable=True)
    playback_provider = Column(String(32), default="youtube")
    playback_id = Column(String(64), nullable=True, index=True)  # YouTube Video ID
    playback_verified = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False, index=True)
    chart_rank = Column(Integer, nullable=True)
    provenance_source = Column(String(128), nullable=False)
    raw_metadata_json = Column(Text, default="{}")
    fetched_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=True)

    interactions = relationship("Interaction", back_populates="track", cascade="all, delete-orphan")
    recommendation_items = relationship("RecommendationItem", back_populates="track", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_tracks_artist_title", "artist", "title"),
    )

class Release(Base):
    __tablename__ = "releases"

    id = Column(String(128), primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    artist = Column(String(256), nullable=False)
    release_date = Column(String(32), nullable=True)
    release_type = Column(String(64), default="Album")
    provider = Column(String(32), nullable=False)
    provider_id = Column(String(128), nullable=False)
    image_url = Column(Text, nullable=True)
    provenance_source = Column(String(128), nullable=False)
    fetched_at = Column(DateTime, default=utc_now)

class ApiCache(Base):
    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(32), nullable=False, index=True)
    endpoint = Column(String(256), nullable=False)
    params_hash = Column(String(64), nullable=False, index=True)
    response_status = Column(Integer, nullable=False)
    payload_json = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    is_stale = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_api_cache_lookup", "source", "endpoint", "params_hash"),
    )

class DemoUser(Base):
    __tablename__ = "demo_users"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    label = Column(String(64), default="SYNTHETIC / DEMO PROFILE")
    bio = Column(Text, nullable=True)
    avatar = Column(String(256), nullable=True)
    preferred_genres = Column(Text, default="[]")  # JSON string
    created_at = Column(DateTime, default=utc_now)

    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    recommendation_runs = relationship("RecommendationRun", back_populates="user", cascade="all, delete-orphan")

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("demo_users.id"), nullable=False, index=True)
    track_id = Column(String(128), ForeignKey("tracks.id"), nullable=False, index=True)
    interaction_type = Column(String(32), nullable=False)  # 'like', 'dislike', 'skip', 'play', 'rate'
    rating_value = Column(Float, nullable=True)
    weight = Column(Float, nullable=False)
    is_synthetic_seed = Column(Boolean, default=False)  # Clearly labels synthetic vs live user interactions
    created_at = Column(DateTime, default=utc_now, index=True)

    user = relationship("DemoUser", back_populates="interactions")
    track = relationship("Track", back_populates="interactions")

    __table_args__ = (
        Index("ix_interactions_user_track", "user_id", "track_id"),
    )

class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("demo_users.id"), nullable=False, index=True)
    data_mode = Column(String(64), default="live_with_synthetic_demo_interactions")
    configured_weights_json = Column(Text, nullable=False)
    effective_weights_json = Column(Text, nullable=False)
    candidate_funnel_json = Column(Text, nullable=False)
    trace_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, index=True)

    user = relationship("DemoUser", back_populates="recommendation_runs")
    items = relationship("RecommendationItem", back_populates="run", cascade="all, delete-orphan")

class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("recommendation_runs.run_id"), nullable=False, index=True)
    track_id = Column(String(128), ForeignKey("tracks.id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    content_score = Column(Float, nullable=False)
    collaborative_score = Column(Float, nullable=False)
    trend_score = Column(Float, nullable=False)
    text_score = Column(Float, nullable=True)
    final_score = Column(Float, nullable=False)
    reasons_json = Column(Text, default="[]")
    is_playback_eligible = Column(Boolean, default=True)

    run = relationship("RecommendationRun", back_populates="items")
    track = relationship("Track", back_populates="recommendation_items")

class SocialDocument(Base):
    __tablename__ = "social_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(64), nullable=False)
    source_url = Column(Text, nullable=False)
    title = Column(String(256), nullable=False)
    summary = Column(Text, nullable=False)
    tokens_json = Column(Text, default="[]")
    sentiment_compound = Column(Float, default=0.0)
    sentiment_label = Column(String(32), default="neutral")
    published_at = Column(DateTime, nullable=True)
    retrieved_at = Column(DateTime, default=utc_now)

class DiagnosticLogEntry(Base):
    __tablename__ = "diagnostic_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), nullable=True, index=True)
    run_id = Column(String(64), nullable=True, index=True)
    level = Column(String(16), nullable=False, index=True)
    method = Column(String(16), nullable=True)
    path = Column(String(256), nullable=True)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Float, nullable=True)
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
