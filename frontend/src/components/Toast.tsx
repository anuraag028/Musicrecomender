import React from 'react';
import { CheckCircle2, AlertCircle, Info, Sparkles } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning';
  title: string;
  subtitle?: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 24,
        right: 24,
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        pointerEvents: 'none',
      }}
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className="animate-fade-in"
          style={{
            pointerEvents: 'auto',
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(16px)',
            border: `1px solid ${t.type === 'success' ? 'rgba(29, 185, 84, 0.4)' : t.type === 'warning' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(139, 92, 246, 0.4)'}`,
            borderRadius: 12,
            padding: '12px 16px',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.6)',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            minWidth: 260,
            maxWidth: 360,
          }}
        >
          <div>
            {t.type === 'success' && <CheckCircle2 size={18} color="#1db954" />}
            {t.type === 'warning' && <AlertCircle size={18} color="#f59e0b" />}
            {t.type === 'info' && <Sparkles size={18} color="#8b5cf6" />}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f8fafc' }}>{t.title}</div>
            {t.subtitle && (
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 2 }}>{t.subtitle}</div>
            )}
          </div>
          <button
            onClick={() => onDismiss(t.id)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#64748b',
              cursor: 'pointer',
              fontSize: '0.8rem',
              padding: '2px 6px',
            }}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};
