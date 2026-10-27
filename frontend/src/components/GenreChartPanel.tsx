import { useEffect, useState } from 'react';
import { ExternalLink, Music2, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { GenreChartResponse, GenreChartTrack } from '../types';
import './GenreChartPanel.css';

const GENRES = [
  { value: 'all', label: 'All genres' },
  { value: 'pop', label: 'Pop' },
  { value: 'rock', label: 'Rock' },
  { value: 'electronic', label: 'Electronic' },
  { value: 'hip-hop', label: 'Hip-Hop' },
  { value: 'indie', label: 'Indie' },
  { value: 'bollywood', label: 'Bollywood' },
  { value: 'jazz', label: 'Jazz' },
  { value: 'classical', label: 'Classical' },
];

type Props = {
  onRecommendTrack?: (track: GenreChartTrack, genre: string) => void;
  onRecommendGenre?: (genre: string) => void;
};

export function GenreChartPanel({ onRecommendTrack, onRecommendGenre }: Props) {
  const [genre, setGenre] = useState('pop');
  const [chart, setChart] = useState<GenreChartResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    setError('');
    setChart(null);
    try {
      const result = await api.getGenreChart(genre);
      setChart(result);
      if (result.status === 'unavailable') setError(result.error || 'The Last.fm chart is unavailable.');
    } catch (reason) {
      const detail = reason instanceof Error ? reason.message : 'Could not load the chart.';
      setError(`${detail} Check that the updated backend is running and LASTFM_API_KEY is configured.`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void refresh(); }, [genre]);

  return <section className="panel genre-chart-panel">
    <div className="section-head">
      <div><p className="eyebrow">LAST.FM TAG CHART</p><h2>Top 10 Trending Tracks</h2></div>
      <div className="genre-chart-actions">
        <select aria-label="Chart genre" value={genre} onChange={event => setGenre(event.target.value)}>
          {GENRES.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        <button className="primary" onClick={() => void refresh()} disabled={loading}><RefreshCw size={15}/>{loading ? 'Refreshing…' : 'Refresh'}</button>
      </div>
    </div>
    <p className="muted chart-methodology">{chart?.methodology || 'Ranked in Last.fm’s selected genre tag chart. This is provider tag popularity, not an official sales or streaming chart.'}</p>
    {onRecommendGenre && <button className="text-button" onClick={() => onRecommendGenre(genre)}>Generate recommendations for {GENRES.find(item => item.value === genre)?.label ?? genre}</button>}
    {loading && <p className="muted">Loading chart from Last.fm…</p>}
    {!loading && error && <div className="chart-error" role="alert"><span>{error}</span><button className="text-button" onClick={() => void refresh()}>Retry</button></div>}
    {!loading && chart?.status === 'empty' && <div className="empty chart-empty"><Music2 size={22}/><b>No chart tracks returned</b><span>Last.fm returned no usable tracks for this selection.</span></div>}
    {!loading && chart?.status === 'ok' && <>
      <p className="muted chart-count">{chart.tracks.length} track{chart.tracks.length === 1 ? '' : 's'} returned{chart.refreshed_at ? ` · refreshed ${new Date(chart.refreshed_at).toLocaleString()}` : ''}</p>
      <div className="track-list chart-track-list">
        {chart.tracks.map(track => <article className="track-row" key={`${track.rank}-${track.artist}-${track.title}`}>
          <span className="track-index">{String(track.rank).padStart(2, '0')}</span>
          <div className="cover-placeholder"><Music2 size={19}/></div>
          <div className="track-meta"><strong>{track.title}</strong><span>{track.artist}</span>
            <small>{track.play_count !== null ? `${track.play_count.toLocaleString()} plays` : 'Play count unavailable'} · {track.listener_count !== null ? `${track.listener_count.toLocaleString()} listeners` : 'Listener count unavailable'}</small>
          </div>
          {onRecommendTrack && <button className="play-button" onClick={() => onRecommendTrack(track, genre)}>Use for recommendations</button>}
          {track.source_url ? <a className="chart-source" href={track.source_url} target="_blank" rel="noreferrer">Last.fm <ExternalLink size={13}/></a> : <span className="metadata-only">Last.fm</span>}
        </article>)}
      </div>
    </>}
    <p className="muted chart-disclaimer">Only tracks returned by Last.fm are shown. Missing counts remain unavailable; no catalogue search or generated entries are substituted.</p>
  </section>;
}
