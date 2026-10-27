import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, SkipForward, Star, Info, Music2 } from 'lucide-react';
import { Track } from '../types';

interface TrackCardProps {
  track: Track;
  isPlaying: boolean;
  isCurrent: boolean;
  onPlay: (track: Track) => void;
  onPause: () => void;
  onInteract: (trackId: string, type: string, ratingValue?: number) => void;
  rank?: number;
  score?: number;
  explainReasons?: string[];
}

export const TrackCard: React.FC<TrackCardProps> = ({
  track,
  isPlaying,
  isCurrent,
  onPlay: _onPlay,
  onPause: _onPause,
  onInteract,
  rank,
  score,
  explainReasons,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [userRating, setUserRating] = useState<number | null>(null);

  const handleRate = (r: number) => {
    setUserRating(r);
    onInteract(track.id, 'rate', r);
  };

  return (
    <div className="music-card" style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Rank badge if present */}
      {rank && (
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: 10,
            background: rank === 1 ? '#eab308' : rank === 2 ? '#94a3b8' : rank === 3 ? '#b45309' : 'rgba(7, 10, 19, 0.85)',
            color: rank <= 3 ? '#000000' : '#ffffff',
            fontWeight: 900,
            fontSize: '0.75rem',
            width: 26,
            height: 26,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10,
            boxShadow: '0 4px 10px rgba(0,0,0,0.5)',
          }}
        >
          #{rank}
        </div>
      )}

      {/* Cover Artwork & Play Overlay */}
      <div style={{ position: 'relative', width: '100%', paddingTop: '100%', background: '#0f172a', overflow: 'hidden' }}>
        {track.image_url ? <img
          src={track.image_url}
          alt={track.title}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        /> : <div style={{position:'absolute',inset:0,display:'grid',placeItems:'center',color:'#ffd8e2',background:'linear-gradient(145deg,#673849,#1d2029 70%,#514050)'}}><Music2 size={42}/></div>}

        {/* Currently Playing Equalizer Badge */}
        {isCurrent && isPlaying && (
          <div
            style={{
              position: 'absolute',
              top: 10,
              right: 10,
              background: 'rgba(7, 10, 19, 0.85)',
              backdropFilter: 'blur(6px)',
              borderRadius: 6,
              padding: '4px 8px',
              display: 'flex',
              alignItems: 'center',
              gap: 3,
              zIndex: 10,
            }}
          >
            <span className="equalizer-bar" style={{ height: 12 }} />
            <span className="equalizer-bar" style={{ height: 16 }} />
            <span className="equalizer-bar" style={{ height: 10 }} />
          </div>
        )}

        {/* Catalogue records are not playable without a linked local file. */}
        <div
          style={{
            position: 'absolute',
            bottom: 12,
            left: 12,
            background: 'rgba(7, 10, 19, 0.85)',
            backdropFilter: 'blur(4px)',
            borderRadius: 4,
            padding: '2px 6px',
            fontSize: '0.62rem',
            fontWeight: 600,
            color: '#d7cbd0',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <Music2 size={11} />
          <span>Metadata only</span>
        </div>
      </div>

      {/* Metadata & Controls */}
      <div style={{ padding: '14px', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <h4
          style={{
            fontSize: '0.9rem',
            fontWeight: 700,
            color: '#f8fafc',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
          title={track.title}
        >
          {track.title}
        </h4>
        <p
          style={{
            fontSize: '0.78rem',
            color: '#94a3b8',
            marginTop: 3,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
          title={track.artist}
        >
          {track.artist}
        </p>

        {/* Match Percentage & Provenance */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 10 }}>
          <span className="badge badge-provenance" style={{ fontSize: '0.62rem' }}>
            {track.provenance_source.split(' ')[0]}
          </span>
          {score !== undefined && (
            <span className="badge badge-match" style={{ fontSize: '0.66rem' }}>
              {(score * 100).toFixed(0)}% Match
            </span>
          )}
        </div>

        {/* Tags / Genres */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
          {(track.genres || []).slice(0, 2).map((g) => (
            <span
              key={g}
              style={{
                fontSize: '0.62rem',
                background: 'rgba(255, 255, 255, 0.05)',
                color: '#cbd5e1',
                padding: '2px 5px',
                borderRadius: 4,
              }}
            >
              {g}
            </span>
          ))}
          {track.listener_count && (
            <span style={{ fontSize: '0.65rem', color: '#64748b', alignSelf: 'center', marginLeft: 'auto' }}>
              {(track.listener_count / 1000).toFixed(0)}k listeners
            </span>
          )}
        </div>

        {/* Action Row: Like, Dislike, Skip, Stars, Info */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderTop: '1px solid rgba(255, 255, 255, 0.06)',
            paddingTop: 10,
            marginTop: 'auto',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <button
              onClick={() => onInteract(track.id, 'like')}
              className="btn-icon"
              title="Like track (+1.0 to profile)"
            >
              <ThumbsUp size={14} />
            </button>
            <button
              onClick={() => onInteract(track.id, 'dislike')}
              className="btn-icon"
              title="Dislike track (-1.0 to profile)"
            >
              <ThumbsDown size={14} />
            </button>
            <button
              onClick={() => onInteract(track.id, 'skip')}
              className="btn-icon"
              title="Skip track (-0.5 penalty)"
            >
              <SkipForward size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleRate(star)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: (userRating || 0) >= star ? '#fbbf24' : '#475569',
                  cursor: 'pointer',
                  padding: 1,
                }}
                title={`Rate ${star} star(s)`}
              >
                <Star size={11} fill={(userRating || 0) >= star ? '#fbbf24' : 'none'} />
              </button>
            ))}
          </div>

          {explainReasons && explainReasons.length > 0 && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="btn-icon"
              style={{ color: showDetails ? '#1db954' : '#94a3b8' }}
              title="Toggle Recommendation Explanation"
            >
              <Info size={14} />
            </button>
          )}
        </div>

        {/* Explanation Popover */}
        {showDetails && explainReasons && (
          <div
            className="animate-fade-in"
            style={{
              background: '#070a13',
              border: '1px solid rgba(29, 185, 84, 0.3)',
              borderRadius: 8,
              padding: '10px 12px',
              marginTop: 10,
              fontSize: '0.72rem',
              color: '#cbd5e1',
            }}
          >
            <div style={{ fontWeight: 800, color: '#1db954', marginBottom: 4 }}>Why this track?</div>
            <ul style={{ paddingLeft: 14, margin: 0, lineHeight: '1.5' }}>
              {explainReasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
