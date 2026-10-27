import React, { useState, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, ListMusic, Video, ExternalLink } from 'lucide-react';
import { Track } from '../types';

interface MusicPlayerProps {
  currentTrack: Track | null;
  isPlaying: boolean;
  onPlayPause: () => void;
  onNext: () => void;
  onPrevious: () => void;
  queue: Track[];
  onSelectFromQueue: (track: Track) => void;
}

export const MusicPlayer: React.FC<MusicPlayerProps> = ({
  currentTrack,
  isPlaying,
  onPlayPause,
  onNext,
  onPrevious,
  queue,
  onSelectFromQueue,
}) => {
  const [showQueue, setShowQueue] = useState(false);
  const [showVideoEmbed, setShowVideoEmbed] = useState(false);
  const [volume, setVolume] = useState(80);
  const [progressSec, setProgressSec] = useState(0);

  // Simulated progress timer for playback feedback
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setProgressSec((prev) => (prev >= 240 ? 0 : prev + 1));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  useEffect(() => {
    setProgressSec(0);
  }, [currentTrack?.id]);

  if (!currentTrack) {
    return null;
  }

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const embedUrl = currentTrack.playback_id
    ? `https://www.youtube-nocookie.com/embed/${currentTrack.playback_id}?autoplay=1&enablejsapi=1&origin=${window.location.origin}`
    : `https://www.youtube-nocookie.com/embed?listType=search&list=${encodeURIComponent(`${currentTrack.artist} - ${currentTrack.title}`)}`;

  return (
    <>
      {/* Floating Queue Drawer */}
      {showQueue && (
        <div
          className="animate-fade-in"
          style={{
            position: 'fixed',
            bottom: 96,
            right: 24,
            width: 340,
            maxHeight: 400,
            background: 'rgba(10, 14, 23, 0.96)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            borderRadius: 14,
            boxShadow: '0 16px 40px rgba(0,0,0,0.7)',
            padding: 16,
            zIndex: 60,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h4 style={{ fontSize: '0.88rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 6 }}>
              <ListMusic size={16} color="#1db954" /> Playback Queue ({queue.length})
            </h4>
            <button onClick={() => setShowQueue(false)} className="btn-icon" style={{ fontSize: '0.75rem' }}>
              ✕
            </button>
          </div>
          <div style={{ overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {queue.map((t, i) => (
              <div
                key={`${t.id}-${i}`}
                onClick={() => onSelectFromQueue(t)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '8px 10px',
                  borderRadius: 8,
                  background: t.id === currentTrack.id ? 'rgba(29, 185, 84, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  border: t.id === currentTrack.id ? '1px solid rgba(29, 185, 84, 0.4)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                }}
              >
                <span style={{ fontSize: '0.72rem', color: '#64748b', width: 16, textAlign: 'center' }}>
                  {t.id === currentTrack.id ? '▶' : i + 1}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: t.id === currentTrack.id ? '#1db954' : '#f1f5f9', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {t.title}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {t.artist}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Floating Miniature YouTube Video Window */}
      {showVideoEmbed && (
        <div
          className="animate-fade-in"
          style={{
            position: 'fixed',
            bottom: 96,
            left: 260,
            width: 360,
            height: 220,
            background: '#000000',
            border: '1px solid rgba(29, 185, 84, 0.4)',
            borderRadius: 14,
            overflow: 'hidden',
            boxShadow: '0 20px 50px rgba(0,0,0,0.9)',
            zIndex: 60,
          }}
        >
          <div style={{ background: '#0a0e17', padding: '6px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#1db954', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Video size={13} /> YouTube IFrame Stream
            </span>
            <button onClick={() => setShowVideoEmbed(false)} className="btn-icon" style={{ padding: 2 }}>
              ✕
            </button>
          </div>
          <iframe
            src={embedUrl}
            title={`${currentTrack.artist} - ${currentTrack.title}`}
            width="100%"
            height="185"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}

      {/* Persistent Bottom Bar Dock */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 86,
          background: 'rgba(7, 10, 18, 0.96)',
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 -10px 30px rgba(0,0,0,0.6)',
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
        }}
      >
        {/* Left: Track Cover & Details */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 240, maxWidth: 360 }}>
          <img
            src={currentTrack.image_url || 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=120'}
            alt={currentTrack.title}
            style={{ width: 54, height: 54, borderRadius: 10, objectFit: 'cover', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}
          />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: '#f8fafc', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {currentTrack.title}
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: 2 }}>
              {currentTrack.artist}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <span className="badge badge-provenance" style={{ fontSize: '0.58rem', padding: '1px 5px' }}>
                {currentTrack.provenance_source.split(' ')[0]}
              </span>
              <span style={{ fontSize: '0.62rem', color: currentTrack.playback_verified ? '#34d399' : '#fbbf24' }}>
                {currentTrack.playback_verified ? 'Verified Audio' : 'Search Embed'}
              </span>
            </div>
          </div>
        </div>

        {/* Center: Controls & Scrubber */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1, maxWidth: 540 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <button onClick={onPrevious} className="btn-icon" title="Previous Track">
              <SkipBack size={19} />
            </button>
            <button
              onClick={onPlayPause}
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: '#1db954',
                color: '#ffffff',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(29, 185, 84, 0.5)',
                transition: 'transform 0.15s ease',
              }}
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause size={19} /> : <Play size={19} style={{ marginLeft: 2 }} />}
            </button>
            <button onClick={onNext} className="btn-icon" title="Next Track">
              <SkipForward size={19} />
            </button>
          </div>

          {/* Scrubber Progress Bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, width: '100%' }}>
            <span style={{ fontSize: '0.68rem', color: '#64748b', width: 32, textAlign: 'right' }}>
              {formatTime(progressSec)}
            </span>
            <div
              style={{
                flex: 1,
                height: 4,
                background: '#1e293b',
                borderRadius: 2,
                cursor: 'pointer',
                position: 'relative',
              }}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const pct = clickX / rect.width;
                setProgressSec(Math.floor(pct * 210));
              }}
            >
              <div
                style={{
                  width: `${(progressSec / 210) * 100}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, #1db954 0%, #34d399 100%)',
                  borderRadius: 2,
                  position: 'relative',
                }}
              />
            </div>
            <span style={{ fontSize: '0.68rem', color: '#64748b', width: 32 }}>
              3:30
            </span>
          </div>
        </div>

        {/* Right: Volume & Tools */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 200, justifyContent: 'flex-end' }}>
          <button
            onClick={() => setShowVideoEmbed(!showVideoEmbed)}
            className="btn-secondary"
            style={{ fontSize: '0.72rem', padding: '5px 10px' }}
            title="Toggle YouTube video player preview"
          >
            <Video size={13} color="#f43f5e" />
            <span>{showVideoEmbed ? 'Hide Video' : 'Video Preview'}</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Volume2 size={16} color="#94a3b8" />
            <input
              type="range"
              min="0"
              max="100"
              value={volume}
              onChange={(e) => setVolume(parseInt(e.target.value))}
              style={{ width: 70 }}
            />
          </div>

          <button
            onClick={() => setShowQueue(!showQueue)}
            className="btn-icon"
            style={{ color: showQueue ? '#1db954' : '#94a3b8' }}
            title="Toggle Playback Queue"
          >
            <ListMusic size={20} />
          </button>
        </div>

        {/* Hidden active audio stream iframe when preview is closed */}
        {!showVideoEmbed && (
          <iframe
            src={isPlaying ? embedUrl : ''}
            title="YouTube Audio Stream"
            style={{ position: 'absolute', width: 1, height: 1, opacity: 0.01, pointerEvents: 'none' }}
            allow="autoplay"
          />
        )}
      </div>
    </>
  );
};
