export function appendUnique<T extends { id: string }>(queue: T[], track: T): T[];
export function insertNext<T extends { id: string }>(queue: T[], currentId: string | null, track: T): T[];
export function removeFromQueue<T extends { id: string }>(queue: T[], trackId: string): T[];
export function makeNowPlayingValue(track: { id: string; title: string; artist: string; album?: string; genre?: string; source: 'local'|'preview' } | null, playing: boolean, currentTime: number, changeEvent: number): import('./NowPlayingContext').NowPlayingValue;
export function makeSeedInput(track: { title: string; artist: string; album?: string; genre?: string } | null): { title: string; artist: string; album: string|null; genre: string|null } | null;
