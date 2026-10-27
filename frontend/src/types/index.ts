export interface Track {
  id: string;
  provider: string;
  provider_id: string;
  title: string;
  artist: string;
  album?: string | null;
  release_date?: string | null;
  genres: string[];
  tags: string[];
  play_count?: number | null;
  listener_count?: number | null;
  duration_ms?: number | null;
  image_url?: string | null;
  playback_provider: string;
  playback_id?: string | null;
  playback_verified: boolean;
  is_trending: boolean;
  chart_rank?: number | null;
  provenance_source: string;
  fetched_at: string;
}

export interface ReleaseItem {
  id: string;
  title: string;
  artist: string;
  release_date?: string | null;
  release_type: string;
  provider: string;
  provider_id: string;
  image_url?: string | null;
  provenance_source: string;
  fetched_at: string;
}

export interface DemoUser {
  id: string;
  name: string;
  label: string;
  bio?: string;
  avatar?: string;
  preferred_genres: string[];
  interaction_count: number;
  created_at: string;
}

export interface UserPreferences {
  user_id: string;
  name: string;
  label: string;
  preferred_genres: string[];
  recent_interactions: Array<{
    id: number;
    track_id: string;
    title: string;
    artist: string;
    interaction_type: string;
    weight: number;
    rating_value?: number | null;
    is_synthetic_seed: boolean;
    created_at: string;
  }>;
  stats: {
    likes: number;
    dislikes: number;
    skips: number;
    plays: number;
    ratings: number;
  };
}

export interface ComponentEvidence {
  score?: number | null;
  weighted_contribution?: number | null;
  available: boolean;
  reason?: string | null;
  evidence: Array<Record<string, any>>;
}

export interface RankedTrack {
  rank: number;
  track_id: string;
  title: string;
  artist: string;
  album?: string | null;
  image_url?: string | null;
  playback_id?: string | null;
  playback_verified: boolean;
  final_score: number;
  components: {
    content: ComponentEvidence;
    collaborative: ComponentEvidence;
    trend: ComponentEvidence;
    text: ComponentEvidence;
  };
  reasons: string[];
  data_sources: string[];
}

export interface CandidateFunnel {
  retrieved: number;
  deduplicated: number;
  excluded_already_played: number;
  excluded_disliked: number;
  excluded_genre?: number;
  excluded_unavailable_playback: number;
  playback_eligible: number;
  scored: number;
  selected: number;
}

export interface RecommendationRunTrace {
  run_id: string;
  user_id: string;
  data_mode: string;
  generated_at: string;
  formula: string;
  configured_weights: Record<string, number>;
  effective_weights: Record<string, number>;
  candidate_funnel: CandidateFunnel;
  ranked_tracks: RankedTrack[];
  exclusions: Array<{
    track_id: string;
    title: string;
    artist: string;
    reason: string;
  }>;
}

export interface RecommendationResponse {
  run_id: string;
  user_id: string;
  generated_at: string;
  count: number;
  effective_weights: Record<string, number>;
  tracks: RankedTrack[];
  funnel: CandidateFunnel;
  trace_url: string;
}

export interface DiagnosticLogItem {
  timestamp: string;
  level: string;
  message: string;
  request_id?: string | null;
  run_id?: string | null;
  method?: string | null;
  path?: string | null;
  status_code?: number | null;
  duration_ms?: number | null;
  details?: Record<string, any> | null;
}

export interface ProviderStatus {
  provider: string;
  status: string;
  is_live: boolean;
  requires_key: boolean;
  key_configured: boolean;
  last_fetch?: string | null;
  cached_records_count: number;
  error_message?: string | null;
  rate_limit_policy: string;
}

export interface TwsmaSummary {
  status: string;
  articles_count: number;
  unique_sources_count: number;
  latest_retrieval?: string | null;
  sentiment_distribution: Record<string, number>;
  top_keywords: Array<{ term: string; count: number }>;
  artist_mentions?: Array<{ artist: string; count: number }>;
  sentiment_trends?: Array<{ date: string; positive: number; neutral: number; negative: number }>;
  methodology: {
    text_preprocessing: string;
    sentiment_model: string;
    term_frequency: string;
    social_signal_derivation: string;
  };
  articles: Array<{
    id: number;
    source_name: string;
    source_url: string;
    title: string;
    summary: string;
    sentiment_compound: number;
    sentiment_label: string;
    top_terms: string[];
    published_at?: string | null;
    retrieved_at?: string | null;
  }>;
}

export interface GenreChartTrack {
  rank: number;
  title: string;
  artist: string;
  play_count: number | null;
  listener_count: number | null;
  source_url: string | null;
}

export interface GenreChartResponse {
  status: 'ok' | 'empty' | 'unavailable';
  provider: string;
  genre: string;
  methodology: string;
  refreshed_at: string | null;
  error: string | null;
  tracks: GenreChartTrack[];
}

export interface SeededRecommendationTrack {
  id: string; title: string; artist: string; album?: string | null; genres: string[]; image_url?: string | null;
  source: string; provider_id?: string | null; preview_url?: string | null; store_url?: string | null;
  playback_availability: 'preview' | 'metadata_only' | 'local'; score: number;
  components: Record<string, ComponentEvidence>; effective_weights: Record<string, number>;
  reasons: string[]; retrieved_at?: string | null;
}

export interface SeededRecommendationResponse {
  seed: { title?: string | null; artist?: string | null; album?: string | null; genre?: string | null };
  generated_at: string; count: number; tracks: SeededRecommendationTrack[];
  apple_discoveries: SeededRecommendationTrack[]; apple_status: 'ok'|'empty'|'unavailable'; apple_error?: string | null;
  effective_weights: Record<string, number>;
  funnel: { retrieved: number; deduplicated: number; filtered: number; ranked: number; apple_relevant: number };
  methodology: string; collaborative_status: string; trend_status: string;
}

export interface TwsmaContextResponse {
  status: 'ok'|'empty'; context: { artist?: string|null; title?: string|null; album?: string|null; genre?: string|null };
  articles_count: number; sentiment_distribution: Record<string, number>;
  articles: Array<{ id:number; source_name:string; source_url:string; title:string; summary:string; sentiment_compound:number; sentiment_label:string; published_at?:string|null; retrieved_at?:string|null; matched_entities:Array<{type:string;name:string}>; relevance_score:number; relevance_reason:string; text_category:string }>;
  social_posts: { status:'unavailable'|'available'; reason?:string|null };
}

export interface AppleSearchTrack {
  id: string; provider_id?: string | null; title: string; artist: string; album?: string | null; genre?: string | null;
  duration_ms?: number | null; image_url?: string | null; preview_url?: string | null; store_url?: string | null; source: string;
}
export interface AppleSearchResponse { status: 'ok'|'empty'|'unavailable'; error?: string | null; retrieved_at?: string | null; tracks: AppleSearchTrack[]; }

