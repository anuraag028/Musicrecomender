from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# ----------------- Track & Release -----------------
class TrackBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    provider_id: str
    title: str
    artist: str
    album: Optional[str] = None
    release_date: Optional[str] = None
    genres: List[str] = []
    tags: List[str] = []
    play_count: Optional[int] = None
    listener_count: Optional[int] = None
    duration_ms: Optional[int] = None
    image_url: Optional[str] = None
    playback_provider: str = "youtube"
    playback_id: Optional[str] = None
    playback_verified: bool = False
    is_trending: bool = False
    chart_rank: Optional[int] = None
    provenance_source: str
    fetched_at: datetime

class ReleaseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    artist: str
    release_date: Optional[str] = None
    release_type: str = "Album"
    provider: str
    provider_id: str
    image_url: Optional[str] = None
    provenance_source: str
    fetched_at: datetime

# ----------------- User & Preferences -----------------
class DemoUserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    label: str
    bio: Optional[str] = None
    avatar: Optional[str] = None
    preferred_genres: List[str] = []
    interaction_count: int = 0
    created_at: datetime

class UserPreferencesResponse(BaseModel):
    user_id: str
    name: str
    label: str
    preferred_genres: List[str]
    recent_interactions: List[Dict[str, Any]]
    stats: Dict[str, Any]

# ----------------- Interaction -----------------
class InteractionCreate(BaseModel):
    user_id: str
    track_id: str
    interaction_type: str = Field(..., description="like, dislike, skip, play, rate")
    rating_value: Optional[float] = Field(None, ge=1.0, le=5.0)

class InteractionResponse(BaseModel):
    id: int
    user_id: str
    track_id: str
    interaction_type: str
    rating_value: Optional[float]
    weight: float
    is_synthetic_seed: bool
    created_at: datetime
    message: str

# ----------------- Recommendation Trace & Explainability -----------------
class ComponentEvidence(BaseModel):
    score: Optional[float]
    weighted_contribution: Optional[float]
    available: bool = True
    reason: Optional[str] = None
    evidence: List[Dict[str, Any]] = []

class RankedTrackExplainability(BaseModel):
    rank: int
    track_id: str
    title: str
    artist: str
    album: Optional[str] = None
    image_url: Optional[str] = None
    playback_id: Optional[str] = None
    playback_verified: bool = False
    final_score: float
    components: Dict[str, ComponentEvidence]
    reasons: List[str] = []
    data_sources: List[str] = []

class CandidateFunnel(BaseModel):
    retrieved: int
    deduplicated: int
    excluded_already_played: int
    excluded_disliked: int
    excluded_unavailable_playback: int
    playback_eligible: int
    scored: int
    selected: int

class RecommendationRunTrace(BaseModel):
    run_id: str
    user_id: str
    data_mode: str = "live_with_synthetic_demo_interactions"
    generated_at: str
    formula: str = "hybrid = sum(effective_weight * available_component_score)"
    configured_weights: Dict[str, float]
    effective_weights: Dict[str, float]
    candidate_funnel: CandidateFunnel
    ranked_tracks: List[RankedTrackExplainability]
    exclusions: List[Dict[str, Any]] = []

class RecommendationGenerateRequest(BaseModel):
    user_id: str
    limit: int = Field(10, ge=1, le=50)
    diversity_penalty: float = Field(0.15, ge=0.0, le=1.0)
    exclude_played: bool = True
    custom_weights: Optional[Dict[str, float]] = None

class RecommendationGenerateResponse(BaseModel):
    run_id: str
    user_id: str
    generated_at: str
    count: int
    effective_weights: Dict[str, float]
    tracks: List[RankedTrackExplainability]
    funnel: CandidateFunnel
    trace_url: str

# ----------------- Diagnostics & Logs -----------------
class DiagnosticLogItem(BaseModel):
    timestamp: str
    level: str
    message: str
    request_id: Optional[str] = None
    run_id: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class ProviderStatus(BaseModel):
    provider: str
    status: str  # 'HEALTHY', 'DEGRADED', 'KEY_REQUIRED', 'RATE_LIMITED', 'DOWN'
    is_live: bool
    requires_key: bool
    key_configured: bool
    last_fetch: Optional[str] = None
    cached_records_count: int = 0
    error_message: Optional[str] = None
    rate_limit_policy: str

class DiagnosticsResponse(BaseModel):
    system_status: str
    timestamp: str
    providers: List[ProviderStatus]
    logs: List[DiagnosticLogItem]

# ----------------- TWSMA Text Analytics -----------------
class TwsmaArticle(BaseModel):
    id: int
    source_name: str
    source_url: str
    title: str
    summary: str
    sentiment_compound: float
    sentiment_label: str
    top_terms: List[str]
    published_at: Optional[str]

class TwsmaSummary(BaseModel):
    status: str
    articles_count: int
    unique_sources_count: int
    latest_retrieval: Optional[str]
    sentiment_distribution: Dict[str, int]
    top_keywords: List[Dict[str, Any]]
    methodology: Dict[str, str]
    articles: List[TwsmaArticle]
