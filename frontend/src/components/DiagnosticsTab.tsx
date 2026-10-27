import React, { useState, useEffect } from 'react';
import { Activity, Server, AlertCircle, CheckCircle2, AlertTriangle, RefreshCw, Filter, FileText } from 'lucide-react';
import { ProviderStatus, DiagnosticLogItem } from '../types';
import { api } from '../api/client';

export const DiagnosticsTab: React.FC = () => {
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [logs, setLogs] = useState<DiagnosticLogItem[]>([]);
  const [levelFilter, setLevelFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const fetchDiagnostics = async () => {
    setIsLoading(true);
    try {
      const [pData, lData] = await Promise.all([
        api.getProvidersStatus(),
        api.getDiagnosticLogs(levelFilter || undefined, 60),
      ]);
      setProviders(pData);
      setLogs(lData);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
    const interval = setInterval(fetchDiagnostics, 8000);
    return () => clearInterval(interval);
  }, [levelFilter]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>System Diagnostics & Structured Logs</h2>
            <span className="badge badge-live">LIVE TELEMETRY</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 4 }}>
            Real external provider connectivity, rate limit policies, cache performance, and structured JSONL logs.
          </p>
        </div>

        <button onClick={fetchDiagnostics} disabled={isLoading} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          <span>Refresh Diagnostics</span>
        </button>
      </div>

      {/* External Providers Health Grid */}
      <div style={{ marginBottom: 28 }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Server size={16} color="#10b981" /> Provider Status & Rate Limits
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
          {providers.map((p) => {
            const isOk = p.status === 'HEALTHY';
            const isWarn = p.status === 'KEY_REQUIRED' || p.status === 'FALLBACK_ACTIVE';
            return (
              <div
                key={p.provider}
                style={{
                  background: 'rgba(15, 23, 42, 0.7)',
                  border: `1px solid ${isOk ? 'rgba(16, 185, 129, 0.3)' : isWarn ? 'rgba(245, 158, 11, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                  borderRadius: 10,
                  padding: '14px 16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h4 style={{ fontSize: '0.86rem', fontWeight: 700, color: '#f1f5f9' }}>{p.provider}</h4>
                  <span
                    className="badge"
                    style={{
                      background: isOk ? 'rgba(16, 185, 129, 0.15)' : isWarn ? 'rgba(245, 158, 11, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                      color: isOk ? '#34d399' : isWarn ? '#fbbf24' : '#fb7185',
                      fontSize: '0.66rem',
                    }}
                  >
                    {p.status}
                  </span>
                </div>

                <div style={{ marginTop: 10, fontSize: '0.74rem', color: '#94a3b8', lineHeight: '1.4' }}>
                  <div>
                    Cached Records: <b style={{ color: '#f8fafc' }}>{p.cached_records_count}</b>
                  </div>
                  <div>
                    Last Polled:{' '}
                    <span style={{ color: '#cbd5e1' }}>
                      {p.last_fetch ? new Date(p.last_fetch).toLocaleTimeString() : 'Not yet polled'}
                    </span>
                  </div>
                  <div style={{ marginTop: 6, color: '#64748b', fontSize: '0.7rem' }}>
                    Policy: {p.rate_limit_policy}
                  </div>
                </div>

                {p.error_message && (
                  <div
                    style={{
                      marginTop: 8,
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid rgba(245, 158, 11, 0.2)',
                      borderRadius: 6,
                      padding: '6px 8px',
                      fontSize: '0.7rem',
                      color: '#fbbf24',
                    }}
                  >
                    {p.error_message}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Structured Logs Section */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileText size={16} color="#38bdf8" />
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
              Structured Backend JSONL Logs ({logs.length})
            </h3>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Filter size={14} color="#94a3b8" />
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="input-dark"
              style={{ fontSize: '0.75rem', padding: '4px 8px' }}
            >
              <option value="">All Severities</option>
              <option value="INFO">INFO Only</option>
              <option value="WARNING">WARNING Only</option>
              <option value="ERROR">ERROR Only</option>
            </select>
          </div>
        </div>

        <div style={{ maxHeight: 420, overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.75rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: '#94a3b8', background: 'rgba(0,0,0,0.2)', position: 'sticky', top: 0 }}>
                <th style={{ padding: '8px 12px' }}>Timestamp</th>
                <th style={{ padding: '8px 12px' }}>Level</th>
                <th style={{ padding: '8px 12px' }}>Message</th>
                <th style={{ padding: '8px 12px' }}>Endpoint</th>
                <th style={{ padding: '8px 12px' }}>Latency</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', fontFamily: 'monospace' }}>
                  <td style={{ padding: '8px 12px', color: '#64748b', whiteSpace: 'nowrap' }}>
                    {new Date(l.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <span
                      style={{
                        color: l.level === 'ERROR' ? '#f87171' : l.level === 'WARNING' ? '#fbbf24' : '#34d399',
                        fontWeight: 700,
                      }}
                    >
                      {l.level}
                    </span>
                  </td>
                  <td style={{ padding: '8px 12px', color: '#e2e8f0', maxWidth: 380, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {l.message}
                  </td>
                  <td style={{ padding: '8px 12px', color: '#38bdf8' }}>
                    {l.path ? `${l.method || 'GET'} ${l.path}` : '-'}
                  </td>
                  <td style={{ padding: '8px 12px', color: '#a5b4fc' }}>
                    {l.duration_ms ? `${l.duration_ms}ms` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
