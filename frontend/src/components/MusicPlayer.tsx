import React from 'react';
import { Music2 } from 'lucide-react';
import type { Track } from '../types';

/** Catalogue entries are metadata only. Local files are played by the browser audio dock in App. */
export const MusicPlayer: React.FC<{ currentTrack: Track | null }> = ({ currentTrack }) => (
  <div className="player-wait">
    <Music2 size={20} />
    {currentTrack
      ? 'This catalogue entry has no local audio file. Import a matching track to play it.'
      : 'Import a local audio file to start listening.'}
  </div>
);
