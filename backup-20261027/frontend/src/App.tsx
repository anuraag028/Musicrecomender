import React, { useEffect, useMemo, useState } from 'react';
import { api } from './api/client';
import type { DemoUser, Track, RankedTrack, PlaybackInfo } from './types';
import { Music2, Search, Play, RefreshCw, Radio, Sparkles, AlertCircle } from 'lucide-react';

type Item = {
  id: string; title: string; artist: string; image_url?: string | null;
  genres?: string[]; provenance_source?: string; final_score?: number;
  components?: RankedTrack['components']; playback_id?: string | null;
};

function asItem(t: Track | RankedTrack): Item {
  if ('track_id' in t) return {
    id: t.track_id, title: t.title, artist: t.artist, image_url: t.image_url,
    final_score: t.final_score, components: t.components, playback_id: t.playback_id
  };
  return { id: t.id, title: t.title, artist: t.artist, image_url: t.image_url,
    genres: t.genres, provenance_source: t.provenance_source, playback_id: t.playback_id };
}

export default function App() {
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [userId, setUserId] = useState('');
  const [trending, setTrending] = useState<Track[]>([]);
  const [recommendations, setRecommendations] = useState<RankedTrack[]>([]);
  const [results, setResults] = useState<Track[]>([]);
  const [query, setQuery] = useState('');
  const [activeTrack, setActiveTrack] = useState<Item | null>(null);
  const [playback, setPlayback] = useState<PlaybackInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('Connecting to backend…');
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [u, t, h] = await Promise.all([api.getDemoUsers(), api.getTrending(12), api.getHealth()]);
        setUsers(u); setTrending(t); setUserId(u[0]?.id ?? '');
        setStatus(`Backend connected · ${h.tracks_in_catalogue} catalogue tracks`);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Could not connect to backend');
        setStatus('Backend unavailable');
      }
    })();
  }, []);

  const selectedUser = useMemo(() => users.find(u => u.id === userId), [users, userId]);

  async function syncRealMusic() {
    setSyncing(true); setError('');
    try {
      await api.syncCatalogue();
      await new Promise(resolve => setTimeout(resolve, 1800));
      const [t, h] = await Promise.all([api.getTrending(12), api.getHealth()]);
      setTrending(t);
      setStatus(`Backend connected · ${h.tracks_in_catalogue} catalogue tracks`);
      if (!t.length) setError('Sync started, but no real chart tracks are available yet. Check provider status/API credentials and try again.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not sync real music');
    } finally { setSyncing(false); }
  }

  async function generate(uid = userId) {
    if (!uid) return;
    setBusy(true); setError('');
    try {
      const response = await api.generateRecommendations(uid, 8, 0.1, true);
      setRecommendations(response.tracks);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Recommendation request failed');
    } finally { setBusy(false); }
  }

  async function searchSongs(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) { setResults([]); return; }
    setBusy(true); setError('');
    try { setResults(await api.searchMusic(query.trim(), 12)); }
    catch (e) { setError(e instanceof Error ? e.message : 'Song search failed'); }
    finally { setBusy(false); }
  }

  async function playInApp(item: Item) {
    setActiveTrack(item);
    setPlayback(null);
    setError('');
    try {
      const info = await api.getTrackPlayback(item.id);
      setPlayback(info);
    } catch (e) {
      setPlayback(null);
      setError(`Could not resolve in-app playback for ${item.title}: ${e instanceof Error ? e.message : 'unknown error'}`);
    }
  }

  const embedUrl = playback?.embed_url || (playback?.playback_id
    ? `https://www.youtube-nocookie.com/embed/${playback.playback_id}?autoplay=1&rel=0`
    : '');

  function TrackRow({ item, index }: { item: Item; index: number }) {
    return <article className="track-row">
      <div className="track-index">{index + 1}</div>
      <img className="cover" src={item.image_url || ''} onError={e => { e.currentTarget.style.visibility = 'hidden'; }} alt="" />
      <div className="track-meta">
        <strong>{item.title}</strong><span>{item.artist}</span>
        {item.genres?.length ? <small>{item.genres.slice(0, 3).join(' · ')}</small> : null}
      </div>
      {typeof item.final_score === 'number' ? <span className="score">{(item.final_score * 100).toFixed(1)}%</span> : null}
      <button className="play-button" onClick={() => void playInApp(item)} title="Play inside this app"><Play size={16} fill="currentColor" /> Play</button>
    </article>;
  }

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand"><span className="brand-icon"><Music2 size={22}/></span><div><b>Music Recommender</b><small>Hybrid recommendations</small></div></div>
      <div className="header-actions"><div className="backend-status"><span className={status.startsWith('Backend connected') ? 'status-dot' : 'status-dot warn'} />{status}</div><button className="sync-button" onClick={() => void syncRealMusic()} disabled={syncing}><RefreshCw size={14} className={syncing ? 'spin' : ''}/>{syncing ? 'Syncing…' : 'Sync real music'}</button></div>
    </header>
    <main className="main">
      <section className="welcome">
        <div><p className="eyebrow">YOUR PERSONAL MUSIC SPACE</p><h1>Find your <em>next favourite.</em></h1><p className="sub">Discover music through your preferences, listening patterns and real chart data.</p></div>
        <div className="user-box"><label htmlFor="demo-user">Demo listener</label><select id="demo-user" value={userId} onChange={e => { setUserId(e.target.value); setRecommendations([]); }}><option value="">Choose user</option>{users.map(u => <option key={u.id} value={u.id}>{u.name} · Demo</option>)}</select><small>{selectedUser?.preferred_genres?.slice(0, 4).join(' · ') || 'Select a demo profile'}</small></div>
      </section>

      {error && <div className="notice"><AlertCircle size={17}/><span>{error}</span><button onClick={() => setError('')}>Dismiss</button></div>}

      <section className="panel search-panel">
        <form onSubmit={searchSongs} className="search-form"><Search size={19}/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search a real song or artist…" aria-label="Search song or artist"/><button className="primary" type="submit" disabled={busy}>{busy ? 'Working…' : 'Search'}</button></form>
        {results.length > 0 && <div className="track-list">{results.map((t, i) => <TrackRow key={t.id} item={asItem(t)} index={i}/>)}</div>}
        {query && !busy && results.length === 0 && <p className="muted">Search the catalogue to find a real track. Results depend on available music sources.</p>}
      </section>

      <section className="section-head"><div><p className="eyebrow">MADE FOR THIS LISTENER</p><h2><Sparkles size={21}/> Recommended for you</h2></div><button className="primary" onClick={() => void generate()} disabled={busy || !userId}><RefreshCw size={16} className={busy ? 'spin' : ''}/>{busy ? 'Generating…' : 'Generate playlist'}</button></section>
      {recommendations.length ? <section className="panel"><div className="track-list">{recommendations.map((t, i) => <TrackRow key={`${t.track_id}-${i}`} item={asItem(t)} index={i}/>)}</div><p className="footnote">Scores are calculated by the backend from available signals. Select a track to load its player here.</p></section> : <section className="empty panel"><Sparkles size={26}/><b>Your personalized playlist will appear here</b><span>Choose a demo listener and generate recommendations.</span><button className="primary" onClick={() => void generate()} disabled={busy || !userId}>Generate playlist</button></section>}

      <section className="section-head"><div><p className="eyebrow">FROM MUSIC CHARTS</p><h2><Radio size={21}/> Trending tracks</h2></div><span className="pill">Source-backed catalogue</span></section>
      <section className="panel"><div className="track-list">{trending.map((t, i) => <TrackRow key={t.id} item={asItem(t)} index={i}/>)}</div>{!trending.length && <p className="muted">No trending tracks are currently cached. Check your backend provider configuration and try again.</p>}</section>

      <section className="section-head"><div><p className="eyebrow">IN-APP PLAYBACK</p><h2><Play size={21}/> Now playing</h2></div></section>
      <section className="player-panel">
        {activeTrack ? <><div className="now-playing-meta"><img className="player-cover" src={activeTrack.image_url || ''} onError={e => { e.currentTarget.style.visibility = 'hidden'; }} alt=""/><div><p className="eyebrow">SELECTED TRACK</p><h3>{activeTrack.title}</h3><span>{activeTrack.artist}</span><small>{playback?.playback_verified ? 'Playback reference resolved' : playback?.status || 'Resolving playback…'}</small></div></div>
          {embedUrl ? <iframe className="music-iframe" src={embedUrl} title={`Play ${activeTrack.title} by ${activeTrack.artist}`} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerPolicy="strict-origin-when-cross-origin" allowFullScreen/> : <div className="player-wait">{playback ? (playback.note || 'No embeddable player was returned for this track.') : 'Resolving an available player…'}</div>}
          <p className="footnote">Music plays inside this application using the provider's embedded player. Playback availability depends on the source, region and embedding permissions.</p>
        </> : <div className="empty"><Play size={26}/><b>Select Play on any track</b><span>The music player will load here without opening another site.</span></div>}
      </section>
      <footer>Demo profiles and initial listening histories are simulated. Song metadata and trend data must come from the configured real providers.</footer>
    </main>
  </div>;
}
