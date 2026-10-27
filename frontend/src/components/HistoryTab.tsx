import React from 'react';
import { History, ThumbsUp, ThumbsDown, SkipForward, Play, Star, Calendar, RefreshCw } from 'lucide-react';
import { UserPreferences } from '../types';

interface HistoryTabProps {
  preferences: UserPreferences | null;
  isLoading: boolean;
  onRefresh: () => void;
}

export const HistoryTab: React.FC<HistoryTabProps> = ({
  preferences,
  isLoading,
  onRefresh,
}) => {
  if (isLoading && !preferences) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
        <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
        <p>Loading interaction history...</p>
      </div>
    );
  }

  if (!preferences) {
    return null;
  }

  const { stats, recent_interactions, name } = preferences;

  const getActionIcon = (type: string) => {
    switch (type) {
      case 'like':
        return <ThumbsUp size={14} color="#10b981" />;
      case 'dislike':
        return <ThumbsDown size={14} color="#f43f5e" />;
      case 'skip':
        return <SkipForward size={14} color="#f59e0b" />;
      case 'play':
        return <Play size={14} color="#38bdf8" />;
      case 'rate':
        return <Star size={14} color="#fbbf24" />;
      default:
        return <History size={14} color="#94a3b8" />;
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>{name}'s Listening History</h2>
            <span className="badge badge-synthetic">DEMO EVALUATOR PROFILE</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Tracks liked, played, rated, or skipped. Initial synthetic seeds are clearly demarcated from real session interactions.
          </p>
        </div>

        <button onClick={onRefresh} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
          <RefreshCw size={14} /> Refresh History
        </button>
      </div>

      {/* Summary Stats Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12, marginBottom: 24 }}>
        <div className="funnel-card">
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981' }}>{stats.likes}</div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Likes (+1.0)</div>
        </div>
        <div className="funnel-card">
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38bdf8' }}>{stats.plays}</div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Plays (+0.5)</div>
        </div>
        <div className="funnel-card">
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f59e0b' }}>{stats.skips}</div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Skips (-0.5)</div>
        </div>
        <div className="funnel-card">
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f43f5e' }}>{stats.dislikes}</div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Dislikes (-1.0)</div>
        </div>
        <div className="funnel-card">
          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fbbf24' }}>{stats.ratings}</div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Ratings (Stars)</div>
        </div>
      </div>

      {/* Interactions Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', fontWeight: 700, fontSize: '0.88rem', color: '#f8fafc' }}>
          Recent Interactions ({recent_interactions.length})
        </div>

        {recent_interactions.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', background: 'rgba(0,0,0,0.2)' }}>
                  <th style={{ padding: '10px 14px' }}>Action</th>
                  <th style={{ padding: '10px 14px' }}>Track</th>
                  <th style={{ padding: '10px 14px' }}>Weight</th>
                  <th style={{ padding: '10px 14px' }}>Provenance</th>
                  <th style={{ padding: '10px 14px' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {recent_interactions.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                      {getActionIcon(item.interaction_type)}
                      <span style={{ textTransform: 'capitalize', color: '#f1f5f9' }}>{item.interaction_type}</span>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ fontWeight: 600, color: '#f8fafc' }}>{item.title}</div>
                      <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>{item.artist}</div>
                    </td>
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: item.weight > 0 ? '#34d399' : '#fb7185' }}>
                      {item.weight > 0 ? `+${item.weight}` : item.weight}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {item.is_synthetic_seed ? (
                        <span className="badge badge-synthetic" style={{ fontSize: '0.62rem' }}>
                          SYNTHETIC SEED
                        </span>
                      ) : (
                        <span className="badge badge-live" style={{ fontSize: '0.62rem' }}>
                          LIVE SESSION
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '10px 14px', color: '#64748b', fontSize: '0.72rem' }}>
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#94a3b8' }}>
            No interactions recorded yet. Like, play, or skip tracks to see them appear here.
          </div>
        )}
      </div>
    </div>
  );
};
