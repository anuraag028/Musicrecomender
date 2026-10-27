import React from 'react';
import { Calendar, Disc, ExternalLink, Music2, RefreshCw } from 'lucide-react';
import { ReleaseItem } from '../types';

interface NewReleasesTabProps {
  releases: ReleaseItem[];
  isLoading: boolean;
  onRefresh: () => void;
}

export const NewReleasesTab: React.FC<NewReleasesTabProps> = ({
  releases,
  isLoading,
  onRefresh,
}) => {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>Genuine New Releases</h2>
            <span className="badge badge-provenance">MUSICBRAINZ WS/2</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Official album and single releases queried from MusicBrainz release catalog with actual release dates.
          </p>
        </div>

        <button onClick={onRefresh} disabled={isLoading} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Refresh Releases</span>
        </button>
      </div>

      {isLoading && releases.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
          <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Retrieving authentic releases from MusicBrainz...</p>
        </div>
      ) : releases.length > 0 ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 18 }}>
          {releases.map((r) => (
            <div key={r.id} className="music-card" style={{ display: 'flex', gap: 14, padding: 12, alignItems: 'center' }}>
              {r.image_url ? <img
                src={r.image_url}
                alt={r.title}
                style={{ width: 72, height: 72, borderRadius: 8, objectFit: 'cover', flexShrink: 0 }}
              /> : <div style={{width:72,height:72,borderRadius:8,flexShrink:0,display:'grid',placeItems:'center',color:'#ffd8e2',background:'linear-gradient(145deg,#673849,#1d2029 70%,#514050)'}}><Music2 size={25}/></div>}
              <div style={{ minWidth: 0, flex: 1 }}>
                <h4 style={{ fontSize: '0.86rem', fontWeight: 700, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {r.title}
                </h4>
                <p style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {r.artist}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.68rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Calendar size={11} /> {r.release_date || 'Recent Release'}
                  </span>
                  <span className="badge badge-provenance" style={{ fontSize: '0.6rem' }}>
                    {r.release_type}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '40px 20px', textAlign: 'center' }}>
          <Disc size={36} color="#38bdf8" style={{ margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>No releases cached yet</h3>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '8px 0 16px 0' }}>
            Click Refresh to fetch genuine recent releases from MusicBrainz.
          </p>
          <button onClick={onRefresh} className="btn-primary">
            Fetch Releases
          </button>
        </div>
      )}
    </div>
  );
};
