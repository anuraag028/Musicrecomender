import React from 'react';
import { UserCheck, RotateCcw, Sparkles } from 'lucide-react';
import { DemoUser } from '../types';

interface DemoUserSelectorProps {
  users: DemoUser[];
  activeUser: DemoUser | null;
  onSelectUser: (user: DemoUser) => void;
  onResetDemo: () => void;
  isResetting: boolean;
}

export const DemoUserSelector: React.FC<DemoUserSelectorProps> = ({
  users,
  activeUser,
  onSelectUser,
  onResetDemo,
  isResetting,
}) => {
  return (
    <div
      className="glass-panel"
      style={{
        padding: '16px 20px',
        marginBottom: 24,
        background: 'linear-gradient(180deg, rgba(18, 24, 38, 0.85) 0%, rgba(12, 16, 23, 0.95) 100%)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#f8fafc' }}>
              Select Synthetic Demo Evaluator
            </h2>
            <span className="badge badge-synthetic">SYNTHETIC PROFILES ONLY</span>
          </div>
          <p style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: 2 }}>
            Switch profiles to observe how different taste vectors alter Content, Collaborative, Trend, and TWSMA scoring.
          </p>
        </div>

        <button
          onClick={onResetDemo}
          disabled={isResetting}
          className="btn-secondary"
          style={{ fontSize: '0.72rem', padding: '5px 12px' }}
          title="Reset synthetic interactions for all 3 demo users back to clean seed state"
        >
          <RotateCcw size={12} className={isResetting ? 'animate-spin' : ''} />
          <span>{isResetting ? 'Resetting...' : 'Reset Demo Seed State'}</span>
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
        {users.map((u) => {
          const isSelected = activeUser?.id === u.id;
          return (
            <div
              key={u.id}
              onClick={() => onSelectUser(u)}
              style={{
                background: isSelected
                  ? 'linear-gradient(135deg, rgba(29, 185, 84, 0.12) 0%, rgba(15, 23, 42, 0.8) 100%)'
                  : 'rgba(15, 23, 42, 0.5)',
                border: `1.5px solid ${isSelected ? '#1db954' : 'rgba(255, 255, 255, 0.08)'}`,
                borderRadius: 10,
                padding: '12px 14px',
                cursor: 'pointer',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: isSelected ? '0 0 16px rgba(29, 185, 84, 0.2)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <img
                  src={u.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120'}
                  alt={u.name}
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: `2px solid ${isSelected ? '#1db954' : 'rgba(255,255,255,0.1)'}`,
                    flexShrink: 0,
                  }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ fontSize: '0.86rem', fontWeight: 800, color: isSelected ? '#1db954' : '#f1f5f9' }}>
                      {u.name}
                    </div>
                    {isSelected && (
                      <span style={{ color: '#1db954', display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.68rem', fontWeight: 700 }}>
                        <UserCheck size={13} /> Active
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 3, lineHeight: '1.3' }}>
                    {u.bio}
                  </p>
                  
                  {/* Genre preference chips */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 8 }}>
                    {u.preferred_genres.slice(0, 3).map((g) => (
                      <span
                        key={g}
                        style={{
                          fontSize: '0.65rem',
                          background: 'rgba(255, 255, 255, 0.06)',
                          color: '#cbd5e1',
                          padding: '2px 6px',
                          borderRadius: 4,
                          fontWeight: 500,
                        }}
                      >
                        {g}
                      </span>
                    ))}
                    <span style={{ fontSize: '0.65rem', color: '#64748b', alignSelf: 'center', marginLeft: 2 }}>
                      ({u.interaction_count} acts)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
