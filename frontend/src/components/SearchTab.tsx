import React, { useState } from 'react';
import { Search as SearchIcon, Music2, RefreshCw } from 'lucide-react';
import { Track } from '../types';
import { TrackCard } from './TrackCard';
import { api } from '../api/client';

interface SearchTabProps {
  onPlayTrack: (track: Track) => void;
  onPause: () => void;
  currentTrackId: string | null;
  isPlaying: boolean;
  onInteract: (trackId: string, type: string, ratingValue?: number) => void;
}

export const SearchTab: React.FC<SearchTabProps> = ({
  onPlayTrack,
  onPause,
  currentTrackId,
  isPlaying,
  onInteract,
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Track[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    try {
      const data = await api.searchMusic(query.trim());
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>Search Real Music Catalogue</h2>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
          Query tracks by title, artist, or genre. If fewer local records exist, queries MusicBrainz live.
        </p>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 10, maxWidth: 600, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <SearchIcon size={18} color="#94a3b8" style={{ position: 'absolute', left: 12, top: 12 }} />
          <input
            type="text"
            className="input-dark"
            placeholder="Search artist (e.g. Coldplay, Radiohead), title, or genre..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ width: '100%', paddingLeft: 38 }}
          />
        </div>
        <button type="submit" disabled={isSearching || !query.trim()} className="btn-primary" style={{ padding: '0 20px' }}>
          {isSearching ? <RefreshCw size={16} className="animate-spin" /> : 'Search'}
        </button>
      </form>

      {/* Results */}
      {isSearching ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
          <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
          <p>Searching catalogue and querying MusicBrainz API...</p>
        </div>
      ) : results.length > 0 ? (
        <div>
          <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: 14 }}>
            Found {results.length} authentic match(es) for "{query}":
          </div>
          <div className="track-grid">
            {results.map((t) => (
              <TrackCard
                key={t.id}
                track={t}
                isPlaying={isPlaying}
                isCurrent={currentTrackId === t.id}
                onPlay={onPlayTrack}
                onPause={onPause}
                onInteract={onInteract}
              />
            ))}
          </div>
        </div>
      ) : hasSearched ? (
        <div className="glass-panel" style={{ padding: '40px 20px', textAlign: 'center' }}>
          <Music2 size={36} color="#64748b" style={{ margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>No matching tracks found</h3>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '8px 0 0 0' }}>
            Try another query term like "rock", "pop", "Coldplay", or "Beatles".
          </p>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '40px 20px', textAlign: 'center', color: '#64748b' }}>
          Enter a song title or artist above to begin searching authentic music catalogue records.
        </div>
      )}
    </div>
  );
};
