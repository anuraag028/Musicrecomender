import React, { useState, useEffect } from 'react';
import { Newspaper, RefreshCw, BarChart3, MessageSquare, ExternalLink, Sparkles, BookOpen } from 'lucide-react';
import { TwsmaSummary } from '../types';
import { api } from '../api/client';

export const TwsmaTab: React.FC = () => {
  const [summary, setSummary] = useState<TwsmaSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const loadSummary = async () => {
    setIsLoading(true);
    try {
      const data = await api.getTwsmaSummary();
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncFeeds = async () => {
    setIsSyncing(true);
    try {
      await api.syncTwsmaFeeds();
      await loadSummary();
    } catch (err) {
      console.error(err);
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  if (isLoading && !summary) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
        <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px auto' }} />
        <p>Loading Text & Social Media Analytics engine...</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>Text, Web & Social Media Analytics (TWSMA)</h2>
            <span className="badge badge-provenance">NLP & SENTIMENT PIPELINE</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Real music journalism and press text ingestion, VADER sentiment polarity analysis, and keyword co-occurrence.
          </p>
        </div>

        <button onClick={handleSyncFeeds} disabled={isSyncing} className="btn-primary" style={{ fontSize: '0.8rem' }}>
          <RefreshCw size={14} className={isSyncing ? 'animate-spin' : ''} />
          <span>{isSyncing ? 'Ingesting Feeds...' : 'Sync Music News Feeds'}</span>
        </button>
      </div>

      {/* Methodology Section */}
      <div className="glass-panel" style={{ padding: '18px 22px', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <BookOpen size={16} color="#38bdf8" />
          <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc' }}>
            Documented TWSMA Analytical Methodology
          </h3>
        </div>
        <p style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.5' }}>
          Music popularity charts reflect listener activity, whereas TWSMA summarizes music-news RSS text. These articles are not social-media posts. Text is cleaned via HTML tag stripping, lowercased, and filtered through an English domain-specific stopword list. Sentiment is computed via the VADER (Valence Aware Dictionary and sEntiment Reasoner) lexicon engine. Artist co-occurrence density is normalized into a bounded text score in [0.0, 1.0].
        </p>

        {summary && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12, marginTop: 14 }}>
            <div style={{ background: '#0a0f1d', padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>PREPROCESSING</div>
              <div style={{ fontSize: '0.74rem', color: '#38bdf8', fontWeight: 600, marginTop: 2 }}>Regex Tokenizer + Stopword Filter</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>SENTIMENT MODEL</div>
              <div style={{ fontSize: '0.74rem', color: '#34d399', fontWeight: 600, marginTop: 2 }}>VADER Compound Valence</div>
            </div>
            <div style={{ background: '#0a0f1d', padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>HYBRID WEIGHT</div>
              <div style={{ fontSize: '0.74rem', color: '#fbbf24', fontWeight: 600, marginTop: 2 }}>0.10 Configured (Dynamic)</div>
            </div>
          </div>
        )}
      </div>

      {/* Metrics Row */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 24 }}>
          <div className="funnel-card">
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#38bdf8' }}>{summary.articles_count}</div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Articles Ingested</div>
          </div>
          <div className="funnel-card">
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#10b981' }}>{summary.sentiment_distribution.positive || 0}</div>
            <div style={{ fontSize: '0.7rem', color: '#34d399', textTransform: 'uppercase', marginTop: 2 }}>Positive Sentiments</div>
          </div>
          <div className="funnel-card">
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#94a3b8' }}>{summary.sentiment_distribution.neutral || 0}</div>
            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 2 }}>Neutral Sentiments</div>
          </div>
          <div className="funnel-card">
            <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f43f5e' }}>{summary.sentiment_distribution.negative || 0}</div>
            <div style={{ fontSize: '0.7rem', color: '#f87171', textTransform: 'uppercase', marginTop: 2 }}>Negative Sentiments</div>
          </div>
        </div>
      )}

      {/* Top Keywords Cloud */}
      {summary && summary.top_keywords.length > 0 && (
        <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: 24 }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', marginBottom: 12 }}>
            Extracted Domain Keywords (Term Frequency)
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {summary.top_keywords.map((kw) => (
              <span
                key={kw.term}
                style={{
                  fontSize: '0.74rem',
                  background: 'rgba(56, 189, 248, 0.1)',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                  padding: '3px 8px',
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <span>{kw.term}</span>
                <b style={{ color: '#bae6fd', fontSize: '0.66rem' }}>{kw.count}</b>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Real Ingested News Articles Table */}
      {summary && summary.articles.length > 0 && (
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', fontWeight: 700, fontSize: '0.88rem', color: '#f8fafc' }}>
            Ingested News Articles & Sentiment Polarity ({summary.articles.length})
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', background: 'rgba(0,0,0,0.2)' }}>
                  <th style={{ padding: '10px 14px' }}>Headline</th>
                  <th style={{ padding: '10px 14px' }}>Top Terms</th>
                  <th style={{ padding: '10px 14px' }}>Compound Valence</th>
                  <th style={{ padding: '10px 14px' }}>Sentiment</th>
                  <th style={{ padding: '10px 14px' }}>Link</th>
                </tr>
              </thead>
              <tbody>
                {summary.articles.map((art) => (
                  <tr key={art.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '10px 14px', maxWidth: 360 }}>
                      <div style={{ fontWeight: 600, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {art.title}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 2 }}>
                        {art.summary}
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {art.top_terms.slice(0, 3).map((term) => (
                          <span key={term} style={{ fontSize: '0.64rem', background: 'rgba(255,255,255,0.06)', padding: '2px 5px', borderRadius: 4, color: '#cbd5e1' }}>
                            {term}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: art.sentiment_compound > 0 ? '#34d399' : art.sentiment_compound < 0 ? '#fb7185' : '#94a3b8' }}>
                      {art.sentiment_compound > 0 ? `+${art.sentiment_compound}` : art.sentiment_compound}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span
                        className="badge"
                        style={{
                          background: art.sentiment_label === 'positive' ? 'rgba(16, 185, 129, 0.15)' : art.sentiment_label === 'negative' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                          color: art.sentiment_label === 'positive' ? '#34d399' : art.sentiment_label === 'negative' ? '#fb7185' : '#cbd5e1',
                          fontSize: '0.64rem',
                        }}
                      >
                        {art.sentiment_label}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <a
                        href={art.source_url}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: '#38bdf8', display: 'flex', alignItems: 'center', gap: 3, textDecoration: 'none' }}
                        title="Read full article on source website"
                      >
                        <ExternalLink size={13} />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
