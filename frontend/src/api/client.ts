import {
  Track,
  ReleaseItem,
  DemoUser,
  UserPreferences,
  RecommendationResponse,
  SeededRecommendationResponse,
  TwsmaContextResponse,
  AppleSearchResponse,
  RecommendationRunTrace,
  DiagnosticLogItem,
  ProviderStatus,
  TwsmaSummary,
  GenreChartResponse,
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) errorDetail = err.detail;
    } catch {
      // ignored
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export const api = {
  // Health
  getHealth: () => fetchJson<{ status: string; database: string; tracks_in_catalogue: number }>(`${API_BASE}/health`),

  // Users
  getDemoUsers: () => fetchJson<DemoUser[]>(`${API_BASE}/users`),
  getUserPreferences: (userId: string) => fetchJson<UserPreferences>(`${API_BASE}/users/${userId}/preferences`),
  resetDemoProfiles: () => fetchJson<{ status: string; message: string }>(`${API_BASE}/users/reset-demo`, { method: 'POST' }),

  // Music
  getTrending: (limit = 25) => fetchJson<Track[]>(`${API_BASE}/music/trending?limit=${limit}`),
  getNewReleases: (limit = 20) => fetchJson<ReleaseItem[]>(`${API_BASE}/music/new-releases?limit=${limit}`),
  searchMusic: (q: string, limit = 20) => fetchJson<Track[]>(`${API_BASE}/music/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  searchApple: (q: string, limit = 20) => fetchJson<AppleSearchResponse>(`${API_BASE}/music/apple-search?q=${encodeURIComponent(q)}&limit=${limit}`),
  getTrackDetail: (trackId: string) => fetchJson<Track>(`${API_BASE}/music/${trackId}`),
  syncCatalogue: () => fetchJson<{ status: string; message: string }>(`${API_BASE}/music/sync`, { method: 'POST' }),

  // Interactions
  recordInteraction: (userId: string, trackId: string, interactionType: string, ratingValue?: number) =>
    fetchJson<{ message: string; id: number; weight: number }>(`${API_BASE}/interactions`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        track_id: trackId,
        interaction_type: interactionType,
        rating_value: ratingValue,
      }),
    }),

  // Recommendations
  generateRecommendations: (
    userId: string,
    limit = 10,
    diversityPenalty = 0.15,
    excludePlayed = true,
    customWeights?: Record<string, number>,
    seed?: { title?: string; artist?: string; genre?: string }
  ) =>
    fetchJson<RecommendationResponse>(`${API_BASE}/recommendations/generate`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        limit,
        diversity_penalty: diversityPenalty,
        exclude_played: excludePlayed,
        custom_weights: customWeights,
        seed_title: seed?.title,
        seed_artist: seed?.artist,
        seed_genre: seed?.genre,
      }),
    }),

  getGenreChart: (genre: string) => fetchJson<GenreChartResponse>(`${API_BASE}/music/genre-chart?genre=${encodeURIComponent(genre)}`),
  getSeedRecommendations: (seed: {title?:string;artist?:string;album?:string|null;genre?:string|null},limit=10,signal?:AbortSignal) => fetchJson<SeededRecommendationResponse>(`${API_BASE}/recommendations/seeded`, {method:'POST',signal,body:JSON.stringify({seed_title:seed.title,seed_artist:seed.artist,seed_album:seed.album,seed_genre:seed.genre,limit})}),
  getTwsmaContext: (seed:{title?:string;artist?:string;album?:string;genre?:string},signal?:AbortSignal) => {const params=new URLSearchParams();if(seed.title)params.set('title',seed.title);if(seed.artist)params.set('artist',seed.artist);if(seed.album)params.set('album',seed.album);if(seed.genre)params.set('genre',seed.genre);return fetchJson<TwsmaContextResponse>(`${API_BASE}/twsma/context?${params.toString()}`,{signal});},

  getRecommendationTrace: (runId: string) => fetchJson<RecommendationRunTrace>(`${API_BASE}/recommendations/${runId}/trace`),
  getLatestTrace: () => fetchJson<RecommendationRunTrace>(`${API_BASE}/recommendations/latest/trace`),

  // Diagnostics & Providers
  getDiagnosticLogs: (level?: string, limit = 50, requestId?: string, runId?: string) => {
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (limit) params.append('limit', limit.toString());
    if (requestId) params.append('request_id', requestId);
    if (runId) params.append('run_id', runId);
    return fetchJson<DiagnosticLogItem[]>(`${API_BASE}/diagnostics/logs?${params.toString()}`);
  },

  getProvidersStatus: () => fetchJson<ProviderStatus[]>(`${API_BASE}/diagnostics/providers`),

  // TWSMA
  getTwsmaSummary: () => fetchJson<TwsmaSummary>(`${API_BASE}/twsma/summary`),
  syncTwsmaFeeds: () => fetchJson<{ status: string; articles_added: number }>(`${API_BASE}/twsma/sync`, { method: 'POST' }),
};
