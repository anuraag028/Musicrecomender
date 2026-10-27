import React from 'react';
import { Flame, RefreshCw } from 'lucide-react';
import { Track } from '../types';
import { TrackCard } from './TrackCard';

interface TrendingTabProps {
  tracks: Track[];
  isLoading: boolean;
  onRefresh: () => void;
  onPlayTrack: (track: Track) => void;
  onPause: () => void;
  currentTrackId: string | null;
  isPlaying: boolean;
  onInteract: (trackId: string, type: string, ratingValue?: number) => void;
}

export const TrendingTab: React.FC<TrendingTabProps> = ({
  tracks,
  isLoading,
  onRefresh,
  onPlayTrack,
  onPause,
  currentTrackId,
  isPlaying,
  onInteract,
}) => {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>Real Global Trending Tracks</h2>
            <span className="badge badge-live">AUTHENTIC CHART DATA</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Sourced directly from Last.fm Chart API (where key configured) or MusicBrainz Curated Queries.
          </p>
        </div>

        <button onClick={onRefresh} disabled={isLoading} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Refresh Charts</span>
        </button>
      </div>

      {isLoading && tracks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
          <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Fetching real trending tracks from catalogue & providers...</p>
        </div>
      ) : tracks.length > 0 ? (
        <div className="track-grid">
          {tracks.map((t, idx) => (
            <TrackCard
              key={t.id}
              track={t}
              rank={t.chart_rank || idx + 1}
              isPlaying={isPlaying}
              isCurrent={currentTrackId === t.id}
              onPlay={onPlayTrack}
              onPause={onPause}
              onInteract={onInteract}
            />
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '40px 20px', textAlign: 'center' }}>
          <Flame size={36} color="#fbbf24" style={{ margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>No trending tracks cached yet</h3>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '8px 0 16px 0' }}>
            Click Refresh to sync authentic chart tracks from external APIs.
          </p>
          <button onClick={onRefresh} className="btn-primary">
            Sync Real Charts
          </button>
        </div>
      )}
    </div>
  );
};
