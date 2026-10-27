export function appendUnique(queue, track) {
  return queue.some(item => item.id === track.id) ? queue : [...queue, track];
}

export function insertNext(queue, currentId, track) {
  const withoutDuplicate = queue.filter(item => item.id !== track.id);
  const currentIndex = withoutDuplicate.findIndex(item => item.id === currentId);
  withoutDuplicate.splice(currentIndex < 0 ? 0 : currentIndex + 1, 0, track);
  return withoutDuplicate;
}

export function removeFromQueue(queue, trackId) {
  return queue.filter(item => item.id !== trackId);
}

export function makeNowPlayingValue(track, playing, currentTime, changeEvent) {
  return {
    trackId: track?.id ?? null,
    title: track?.title ?? null,
    artist: track?.artist ?? null,
    album: track?.album && track.album !== 'Unknown' ? track.album : null,
    genre: track?.genre && track.genre !== 'Unknown' ? track.genre : null,
    source: track?.source ?? null,
    playing,
    currentTime,
    changeEvent,
  };
}

export function makeSeedInput(track) {
  if (!track) return null;
  return {
    title: track.title || '',
    artist: track.artist || '',
    album: track.album && track.album !== 'Unknown' ? track.album : null,
    genre: track.genre && track.genre !== 'Unknown' ? track.genre : null,
  };
}
