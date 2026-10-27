import { createContext, useContext } from 'react';

export interface NowPlayingValue {
  trackId: string | null;
  title: string | null;
  artist: string | null;
  album: string | null;
  genre: string | null;
  source: 'local' | 'preview' | null;
  playing: boolean;
  currentTime: number;
  changeEvent: number;
}

export const NowPlayingContext = createContext<NowPlayingValue>({
  trackId: null, title: null, artist: null, album: null, genre: null,
  source: null, playing: false, currentTime: 0, changeEvent: 0,
});

export function useNowPlaying() { return useContext(NowPlayingContext); }
