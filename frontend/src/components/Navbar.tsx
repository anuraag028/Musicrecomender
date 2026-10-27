import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle2, AlertTriangle, AlertCircle, Users } from 'lucide-react';
import { DemoUser, ProviderStatus } from '../types';
import { api } from '../api/client';

interface NavbarProps {
  activeTabTitle: string;
  activeUser: DemoUser | null;
  onToggleUserSelector: () => void;
  showUserSelector: boolean;
  onRefreshData: () => void;
  isSyncing: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTabTitle,
  activeUser,
  onToggleUserSelector,
  showUserSelector,
  onRefreshData,
  isSyncing,
}) => {
  const [providers, setProviders] = useState<ProviderStatus[]>([]);

  useEffect(() => {
    api.getProvidersStatus()
      .then(setProviders)
      .catch(() => {});
  }, []);

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 30,
        height: 64,
        background: 'rgba(7, 9, 14, 0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
      }}
    >
      {/* Current View Title */}
      <div>
        <h1 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
          {activeTabTitle}
        </h1>
      </div>

      {/* Right Tools: Provider Health Pills + Sync + Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Provider Status Indicator Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {providers.map((p) => {
            const isOk = p.status === 'HEALTHY';
            const isWarning = p.status === 'KEY_REQUIRED' || p.status === 'FALLBACK_ACTIVE';
            const label = p.provider.includes('MusicBrainz')
              ? 'MusicBrainz'
              : p.provider.includes('Last.fm')
              ? 'Last.fm'
              : 'Music news RSS';

            return (
              <div
                key={p.provider}
                title={`${p.provider} (${p.status}): ${p.rate_limit_policy}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  background: 'rgba(15, 23, 42, 0.7)',
                  border: `1px solid ${isOk ? 'rgba(29, 185, 84, 0.3)' : isWarning ? 'rgba(245, 158, 11, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                  padding: '3px 8px',
                  borderRadius: 20,
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  color: isOk ? '#34d399' : isWarning ? '#fbbf24' : '#f87171',
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: isOk ? '#1db954' : isWarning ? '#f59e0b' : '#f43f5e',
                    display: 'inline-block',
                  }}
                />
                <span>{label}</span>
              </div>
            );
          })}
        </div>

        {/* Sync Data Button */}
        <button
          onClick={onRefreshData}
          disabled={isSyncing}
          className="btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 14px' }}
          title="Fetch latest music chart tracks and RSS articles"
        >
          <RefreshCw size={13} className={isSyncing ? 'animate-spin' : ''} />
          <span>{isSyncing ? 'Syncing...' : 'Sync Catalogue'}</span>
        </button>

        {/* Switch Demo Profiles Toggle Button */}
        <button
          onClick={onToggleUserSelector}
          className="btn-secondary"
          style={{
            fontSize: '0.78rem',
            padding: '6px 14px',
            borderColor: showUserSelector ? '#1db954' : undefined,
            color: showUserSelector ? '#1db954' : undefined,
          }}
          title="Toggle Demo User Switcher Bar"
        >
          <Users size={14} />
          <span>Demo Profiles</span>
        </button>
      </div>
    </header>
  );
};
