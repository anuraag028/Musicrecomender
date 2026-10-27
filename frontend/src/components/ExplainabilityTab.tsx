import React, { useState } from 'react';
import { Copy, Check, Filter, Sparkles, AlertCircle, BarChart3, Database } from 'lucide-react';
import { RecommendationRunTrace } from '../types';

interface ExplainabilityTabProps {
  trace: RecommendationRunTrace | null;
  isLoading: boolean;
}

export const ExplainabilityTab: React.FC<ExplainabilityTabProps> = ({
  trace,
  isLoading,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyJson = () => {
    if (!trace) return;
    navigator.clipboard.writeText(JSON.stringify(trace, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading && !trace) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
        <p>Loading recommendation trace...</p>
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="glass-panel" style={{ padding: '64px 20px', textAlign: 'center' }}>
        <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(148, 163, 184, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
          <AlertCircle size={28} color="#64748b" />
        </div>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc' }}>
          No recommendation run trace available yet
        </h3>
        <p style={{ fontSize: '0.84rem', color: '#94a3b8', margin: '8px auto 0 auto', maxWidth: 460 }}>
          Go to the 'For You' section and click 'Generate My Playlist' to produce a reproducible numeric trace.
        </p>
      </div>
    );
  }

  const { candidate_funnel, configured_weights, effective_weights, ranked_tracks, formula, run_id } = trace;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 900, color: '#f8fafc', letterSpacing: '-0.02em' }}>
              Mathematical Explainability & Run Telemetry
            </h2>
            <span className="badge badge-provenance">DETERMINISTIC FORMULA</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Verifiable scoring decomposition, dynamic runtime weight renormalization, and candidate selection funnel.
          </p>
        </div>

        <button onClick={handleCopyJson} className="btn-secondary" style={{ fontSize: '0.78rem' }}>
          {copied ? <Check size={14} color="#1db954" /> : <Copy size={14} />}
          <span>{copied ? 'Copied Trace JSON' : 'Copy Full Trace JSON'}</span>
        </button>
      </div>

      {/* Formula Card */}
      <div className="glass-panel" style={{ padding: '18px 22px', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Sparkles size={16} color="#1db954" />
          <h3 style={{ fontSize: '0.9rem', fontWeight: 800, color: '#f8fafc' }}>
            Hybrid Scoring Model & Renormalization Theorem
          </h3>
        </div>
        <div style={{ background: '#050811', padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)', fontFamily: 'monospace', fontSize: '0.86rem', color: '#34d399' }}>
          {formula}
        </div>
        <p style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: 8 }}>
          * When any signal is missing (e.g. cold-start target user or no recent press mentions), active weights dynamically scale so their sum is strictly 1.00. No synthetic or guessed values are ever imputed.
        </p>
      </div>

      {/* Candidate Selection Funnel */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800, color: '#f8fafc', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Filter size={15} color="#06b6d4" /> Candidate Selection Funnel
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
          <div className="glass-panel" style={{ padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#06b6d4' }}>{candidate_funnel.retrieved}</div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 3, fontWeight: 700 }}>Retrieved</div>
          </div>
          <div className="glass-panel" style={{ padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#8b5cf6' }}>{candidate_funnel.deduplicated}</div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 3, fontWeight: 700 }}>Deduplicated</div>
          </div>
          <div className="glass-panel" style={{ padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#f59e0b' }}>
              {candidate_funnel.excluded_already_played + candidate_funnel.excluded_disliked}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 3, fontWeight: 700 }}>Excluded</div>
          </div>
          <div className="glass-panel" style={{ padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#38bdf8' }}>{candidate_funnel.playback_eligible}</div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 3, fontWeight: 700 }}>Eligible</div>
          </div>
          <div className="glass-panel" style={{ padding: '14px', textAlign: 'center' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#10b981' }}>{candidate_funnel.scored}</div>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', textTransform: 'uppercase', marginTop: 3, fontWeight: 700 }}>Scored</div>
          </div>
          <div className="glass-panel" style={{ padding: '14px', textAlign: 'center', borderColor: 'rgba(29, 185, 84, 0.4)', background: 'rgba(29, 185, 84, 0.08)' }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#1db954' }}>{candidate_funnel.selected}</div>
            <div style={{ fontSize: '0.68rem', color: '#1db954', textTransform: 'uppercase', marginTop: 3, fontWeight: 800 }}>Selected</div>
          </div>
        </div>
      </div>

      {/* Weights: Configured vs Effective */}
      <div className="glass-panel" style={{ padding: '18px 22px', marginBottom: 24 }}>
        <h3 style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f8fafc', marginBottom: 14 }}>
          Weights: Configured vs Effective Dynamic Renormalization
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          {['content', 'collaborative', 'trend', 'text'].map((cName) => {
            const conf = configured_weights[cName] || 0;
            const eff = effective_weights[cName] || 0;
            const color = cName === 'content' ? '#1db954' : cName === 'collaborative' ? '#38bdf8' : cName === 'trend' ? '#f59e0b' : '#8b5cf6';

            return (
              <div key={cName} style={{ background: '#0a0f1d', padding: '12px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 800, textTransform: 'capitalize' }}>
                  <span style={{ color: '#f8fafc' }}>{cName}</span>
                  <span style={{ color: eff > 0 ? color : '#64748b' }}>
                    {eff > 0 ? `${(eff * 100).toFixed(0)}% Eff` : 'Unavailable'}
                  </span>
                </div>
                <div style={{ marginTop: 6, fontSize: '0.72rem', color: '#94a3b8' }}>
                  Configured: {(conf * 100).toFixed(0)}%
                </div>
                <div style={{ height: 6, background: '#1e293b', borderRadius: 3, marginTop: 6, overflow: 'hidden' }}>
                  <div style={{ width: `${eff * 100}%`, height: '100%', background: color, borderRadius: 3 }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Trace Table */}
      <div className="glass-panel" style={{ overflow: 'hidden', marginBottom: 24 }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', fontWeight: 800, fontSize: '0.88rem', color: '#f8fafc' }}>
          Ranked Component Score Decomposition ({ranked_tracks.length} tracks)
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', background: 'rgba(0,0,0,0.2)' }}>
                <th style={{ padding: '10px 14px' }}>Rank</th>
                <th style={{ padding: '10px 14px' }}>Track</th>
                <th style={{ padding: '10px 14px' }}>Content</th>
                <th style={{ padding: '10px 14px' }}>Collab</th>
                <th style={{ padding: '10px 14px' }}>Trend</th>
                <th style={{ padding: '10px 14px' }}>TWSMA</th>
                <th style={{ padding: '10px 14px' }}>Final Score</th>
              </tr>
            </thead>
            <tbody>
              {ranked_tracks.map((item) => (
                <tr key={item.track_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 900, color: '#38bdf8' }}>#{item.rank}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ fontWeight: 700, color: '#f8fafc' }}>{item.title}</div>
                    <div style={{ color: '#94a3b8', fontSize: '0.72rem' }}>{item.artist}</div>
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {item.components.content?.available ? (
                      <div>
                        <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{item.components.content.score?.toFixed(2)}</span>
                        <div style={{ color: '#1db954', fontSize: '0.68rem' }}>
                          +{item.components.content.weighted_contribution?.toFixed(2)}
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: '#64748b' }}>N/A</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {item.components.collaborative?.available ? (
                      <div>
                        <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{item.components.collaborative.score?.toFixed(2)}</span>
                        <div style={{ color: '#38bdf8', fontSize: '0.68rem' }}>
                          +{item.components.collaborative.weighted_contribution?.toFixed(2)}
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: '#64748b' }}>Cold-Start</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {item.components.trend?.available ? (
                      <div>
                        <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{item.components.trend.score?.toFixed(2)}</span>
                        <div style={{ color: '#f59e0b', fontSize: '0.68rem' }}>
                          +{item.components.trend.weighted_contribution?.toFixed(2)}
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: '#64748b' }}>N/A</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    {item.components.text?.available ? (
                      <div>
                        <span style={{ color: '#8b5cf6', fontWeight: 700 }}>{item.components.text.score?.toFixed(2)}</span>
                        <div style={{ color: '#c4b5fd', fontSize: '0.68rem' }}>
                          +{item.components.text.weighted_contribution?.toFixed(2)}
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.7rem' }}>No press mentions</span>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px', fontWeight: 900, color: '#1db954', fontSize: '0.9rem' }}>
                    {(item.final_score * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Raw Trace JSON */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <h3 style={{ fontSize: '0.88rem', fontWeight: 800, color: '#f8fafc' }}>Full Raw Diagnostic JSON Trace</h3>
          <button onClick={handleCopyJson} className="btn-secondary" style={{ fontSize: '0.72rem', padding: '4px 10px' }}>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <pre className="json-box">{JSON.stringify(trace, null, 2)}</pre>
      </div>
    </div>
  );
};
