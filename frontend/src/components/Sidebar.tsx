import React from 'react';
import {
  Sparkles,
  Flame,
  Disc,
  Search,
  History,
  HelpCircle,
  Activity,
  Newspaper,
  Music,
  UserCheck,
  Radio,
  BarChart2
} from 'lucide-react';
import { DemoUser } from '../types';

export type TabKey = 'for_you' | 'trending' | 'new_releases' | 'search' | 'history' | 'explainability' | 'diagnostics' | 'twsma';

interface SidebarProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  activeUser: DemoUser | null;
  onOpenUserModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  activeUser,
  onOpenUserModal,
}) => {
  return (
    <aside
      style={{
        width: 240,
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        background: '#070a12',
        borderRight: '1px solid rgba(255, 255, 255, 0.06)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 40,
        padding: '20px 14px 96px 14px',
        overflowY: 'auto',
      }}
    >
      {/* Brand Header */}
      <div style={{ padding: '0 8px 24px 8px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: 'linear-gradient(135deg, #1db954 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 14px rgba(29, 185, 84, 0.35)',
          }}
        >
          <Music size={20} color="#ffffff" />
        </div>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 900, letterSpacing: '-0.02em', color: '#ffffff' }}>
            SoundMatrix
          </div>
          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#1db954', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            TWSMA Hybrid AI
          </div>
        </div>
      </div>

      {/* Navigation Groups */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Discover */}
        <div>
          <div style={{ fontSize: '0.68rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 12px 8px 12px' }}>
            Discover
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <button
              onClick={() => onSelectTab('for_you')}
              className={`nav-item ${activeTab === 'for_you' ? 'active' : ''}`}
            >
              <Sparkles size={17} color={activeTab === 'for_you' ? '#1db954' : '#94a3b8'} />
              <span>For You</span>
            </button>
            <button
              onClick={() => onSelectTab('trending')}
              className={`nav-item ${activeTab === 'trending' ? 'active' : ''}`}
            >
              <Flame size={17} color={activeTab === 'trending' ? '#f59e0b' : '#94a3b8'} />
              <span>Trending Charts</span>
            </button>
            <button
              onClick={() => onSelectTab('new_releases')}
              className={`nav-item ${activeTab === 'new_releases' ? 'active' : ''}`}
            >
              <Disc size={17} color={activeTab === 'new_releases' ? '#06b6d4' : '#94a3b8'} />
              <span>New Releases</span>
            </button>
            <button
              onClick={() => onSelectTab('search')}
              className={`nav-item ${activeTab === 'search' ? 'active' : ''}`}
            >
              <Search size={17} color={activeTab === 'search' ? '#8b5cf6' : '#94a3b8'} />
              <span>Search Music</span>
            </button>
          </div>
        </div>

        {/* User Activity */}
        <div>
          <div style={{ fontSize: '0.68rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 12px 8px 12px' }}>
            My Music
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <button
              onClick={() => onSelectTab('history')}
              className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
            >
              <History size={17} color={activeTab === 'history' ? '#38bdf8' : '#94a3b8'} />
              <span>Listening History</span>
            </button>
          </div>
        </div>

        {/* Intelligence & Analytics */}
        <div>
          <div style={{ fontSize: '0.68rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 12px 8px 12px' }}>
            Analytics & Trace
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <button
              onClick={() => onSelectTab('explainability')}
              className={`nav-item ${activeTab === 'explainability' ? 'active' : ''}`}
            >
              <BarChart2 size={17} color={activeTab === 'explainability' ? '#10b981' : '#94a3b8'} />
              <span>Math Explainability</span>
            </button>
            <button
              onClick={() => onSelectTab('twsma')}
              className={`nav-item ${activeTab === 'twsma' ? 'active' : ''}`}
            >
              <Newspaper size={17} color={activeTab === 'twsma' ? '#f43f5e' : '#94a3b8'} />
              <span>TWSMA Social News</span>
            </button>
            <button
              onClick={() => onSelectTab('diagnostics')}
              className={`nav-item ${activeTab === 'diagnostics' ? 'active' : ''}`}
            >
              <Activity size={17} color={activeTab === 'diagnostics' ? '#38bdf8' : '#94a3b8'} />
              <span>Backend Telemetry</span>
            </button>
          </div>
        </div>
      </div>

      {/* Active Demo User Footer Card */}
      {activeUser && (
        <div
          onClick={onOpenUserModal}
          style={{
            marginTop: 'auto',
            background: 'rgba(18, 24, 38, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 10,
            padding: '10px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          title="Click to switch between Alex, Beatrix, or Charlie"
        >
          <img
            src={activeUser.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'}
            alt={activeUser.name}
            style={{ width: 34, height: 34, borderRadius: '50%', objectFit: 'cover', border: '2px solid #1db954' }}
          />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {activeUser.name}
            </div>
            <div style={{ fontSize: '0.66rem', color: '#1db954', display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#1db954', display: 'inline-block' }} />
              Active Demo Profile
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
