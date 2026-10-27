import React, { useState } from 'react';
import { Sparkles, Sliders, Play, RotateCcw, Music } from 'lucide-react';
import { DemoUser, RankedTrack, CandidateFunnel, Track } from '../types';
import { TrackCard } from './TrackCard';

interface ForYouTabProps {
  activeUser: DemoUser | null;
  recommendations: RankedTrack[];
  funnel: CandidateFunnel | null;
  effectiveWeights: Record<string, number> | null;
  isGenerating: boolean;
  onGenerate: (diversity: number, excludePlayed: boolean) => void;
  onPlayTrack: (track: Track) => void;
  onPause: () => void;
  currentTrackId: string | null;
  isPlaying: boolean;
  onInteract: (trackId: string, type: string, ratingValue?: number) => void;
}

export const ForYouTab: React.FC<ForYouTabProps> = ({
  activeUser,
  recommendations,
  effectiveWeights,
  isGenerating,
  onGenerate,
  onPlayTrack,
  onPause,
  currentTrackId,
  isPlaying,
  onInteract,
}) => {
  const [diversity, setDiversity] = useState(0.15);
  const [excludePlayed, setExcludePlayed] = useState(true);

  return (
    <div>
      {/* Hero Banner Card */}
      <div
        className="glass-panel"
        style={{
          padding: '24px 28px',
          marginBottom: 24,
          background: 'radial-gradient(ellipse 100% 120% at 20% 0%, rgba(29, 185, 84, 0.15) 0%, rgba(139, 92, 246, 0.12) 50%, rgba(12, 16, 23, 0.95) 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="badge badge-match" style={{ fontSize: '0.72rem', padding: '3px 10px' }}>
                HYBRID RECOMMENDER AI
              </span>
              <span className="badge badge-synthetic">
                EVALUATOR MODE
              </span>
            </div>
            <h2 style={{ fontSize: '1.45rem', fontWeight: 900, color: '#f8fafc', marginTop: 8, letterSpacing: '-0.02em' }}>
              Personalized Sound Mix for {activeUser?.name || 'Evaluator'}
            </h2>
            <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: 4, maxWidth: 600, lineHeight: '1.4' }}>
              Blends content similarity, collaborative filtering, provider chart data when available, and music-news RSS sentiment into a deterministic ranked list.
            </p>
          </div>

          <button
            onClick={() => onGenerate(diversity, excludePlayed)}
            disabled={isGenerating}
            className="btn-primary"
            style={{ fontSize: '0.92rem', padding: '12px 24px' }}
          >
            <Sparkles size={18} className={isGenerating ? 'animate-spin' : ''} />
            <span>{isGenerating ? 'Computing Hybrid Ranks...' : 'Generate My Playlist'}</span>
          </button>
        </div>

        {/* Algorithm Tuning Controls */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            marginTop: 20,
            paddingTop: 16,
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Sliders size={14} color="#94a3b8" />
            <label style={{ fontSize: '0.78rem', color: '#cbd5e1', fontWeight: 600 }}>
              Artist Diversity Penalty: <span style={{ color: '#1db954', fontWeight: 800 }}>{diversity.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="0"
              max="0.5"
              step="0.05"
              value={diversity}
              onChange={(e) => setDiversity(parseFloat(e.target.value))}
              style={{ width: 100 }}
            />
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.78rem', color: '#cbd5e1', cursor: 'pointer', fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={excludePlayed}
              onChange={(e) => setExcludePlayed(e.target.checked)}
              style={{ accentColor: '#1db954', width: 15, height: 15 }}
            />
            <span>Exclude Already Played / Disliked Tracks</span>
          </label>

          {effectiveWeights && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700 }}>Effective Weights:</span>
              {Object.entries(effectiveWeights).map(([k, w]) => (
                <span
                  key={k}
                  style={{
                    fontSize: '0.68rem',
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    padding: '2px 8px',
                    borderRadius: 12,
                    color: '#e2e8f0',
                  }}
                >
                  {k}: <b style={{ color: '#1db954' }}>{(w * 100).toFixed(0)}%</b>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recommended Track Grid */}
      {recommendations.length > 0 ? (
        <div className="track-grid">
          {recommendations.map((item) => {
            const trackObj: Track = {
              id: item.track_id,
              provider: 'hybrid',
              provider_id: item.track_id,
              title: item.title,
              artist: item.artist,
              album: item.album,
              image_url: item.image_url,
              playback_provider: 'catalogue_only',
              playback_id: item.playback_id,
              playback_verified: item.playback_verified,
              is_trending: false,
              provenance_source: item.data_sources[0] || 'MusicBrainz WS/2',
              genres: [],
              tags: [],
              fetched_at: new Date().toISOString(),
            };

            return (
              <TrackCard
                key={item.track_id}
                track={trackObj}
                rank={item.rank}
                score={item.final_score}
                explainReasons={item.reasons}
                isPlaying={isPlaying}
                isCurrent={currentTrackId === item.track_id}
                onPlay={onPlayTrack}
                onPause={onPause}
                onInteract={onInteract}
              />
            );
          })}
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '64px 20px', textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(29, 185, 84, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
            <Sparkles size={28} color="#1db954" />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc' }}>
            No recommendations generated yet
          </h3>
          <p style={{ fontSize: '0.84rem', color: '#94a3b8', maxWidth: 460, margin: '8px auto 20px auto', lineHeight: '1.4' }}>
            Click 'Generate My Playlist' to compute hybrid recommendations tailored specifically to {activeUser?.name}'s profile.
          </p>
          <button
            onClick={() => onGenerate(diversity, excludePlayed)}
            className="btn-primary"
            disabled={isGenerating}
          >
            Generate My Playlist Now
          </button>
        </div>
      )}
    </div>
  );
};
