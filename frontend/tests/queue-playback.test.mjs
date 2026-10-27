import test from 'node:test';
import assert from 'node:assert/strict';
import { appendUnique, insertNext, makeNowPlayingValue, makeSeedInput, removeFromQueue } from '../src/playback/queueLogic.mjs';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const track = (id, extra = {}) => ({ id, title: `Track ${id}`, artist: 'Test Artist', source: 'local', ...extra });

test('Add to Queue appends once and does not duplicate an existing item', () => {
  const initial = [track('a')];
  assert.deepEqual(appendUnique(appendUnique(initial, track('b')), track('b')).map(item => item.id), ['a', 'b']);
});

test('Play Next inserts after the current item without changing other order', () => {
  assert.deepEqual(insertNext([track('a'), track('b'), track('c')], 'b', track('x')).map(item => item.id), ['a', 'b', 'x', 'c']);
});

test('Play Next places an item first if the current item is not queued', () => {
  assert.deepEqual(insertNext([track('a'), track('b')], 'missing', track('x')).map(item => item.id), ['x', 'a', 'b']);
});

test('Remove deletes only the selected queue item', () => {
  assert.deepEqual(removeFromQueue([track('a'), track('b'), track('c')], 'b').map(item => item.id), ['a', 'c']);
});

test('playback context follows the actual current track, source, state, and time', () => {
  assert.deepEqual(makeNowPlayingValue(track('a', { title: 'Seed Song', artist: 'Seed Artist', album: 'Album', genre: 'Jazz', source: 'preview' }), true, 12.5, 3), {
    trackId: 'a', title: 'Seed Song', artist: 'Seed Artist', album: 'Album', genre: 'Jazz', source: 'preview', playing: true, currentTime: 12.5, changeEvent: 3,
  });
});

test('recommendation seed uses the selected track actual metadata and handles missing tags', () => {
  assert.deepEqual(makeSeedInput(track('local-1', { title: 'Actual Title', artist: 'Actual Artist', album: 'Actual Album', genre: 'Jazz' })), {
    title: 'Actual Title', artist: 'Actual Artist', album: 'Actual Album', genre: 'Jazz',
  });
  assert.deepEqual(makeSeedInput(track('local-2', { album: 'Unknown', genre: 'Unknown' })), {
    title: 'Track local-2', artist: 'Test Artist', album: null, genre: null,
  });
});

test('the shared context and progress are wired to the real HTMLAudioElement', () => {
  const app = readFileSync(resolve(import.meta.dirname, '../src/App.tsx'), 'utf8');
  assert.match(app, /NowPlayingContext\.Provider value=\{makeNowPlayingValue\(current,playing,currentTime,changeEvent\)\}/);
  assert.match(app, /useRef<HTMLAudioElement>\(null\)/);
  assert.match(app, /<audio ref=\{audio\}[\s\S]*?onTimeUpdate=\{e => setCurrentTime\(e\.currentTarget\.currentTime\)\}/);
  assert.match(app, /onLoadedMetadata=\{e => setDuration\(e\.currentTarget\.duration/);
});
