# Viva Guide: Local Music Recommender and TWSMA

## Five-minute demo

1. **Local library:** Import two or more audio files. Show that file metadata and duration appear, and that imported audio plays in the dock. Explain that the browser stores the files in IndexedDB and does not upload them.
2. **Local recommendations:** Open Similar Songs, choose a song, and explain the TF-IDF cosine score, matching metadata, and missing-metadata behavior. Like more than one track to combine preferences. Open Genre Playlists for tracks with genre tags.
3. **Search and charts:** Search a familiar song title or artist. Explain that MusicBrainz and Last.fm provide metadata, not audio. Search records are not playable unless a matching local file is linked. Trending is shown only for Last.fm chart data returned by the configured API.
4. **Hybrid recommendations:** Choose a demo profile under For You and generate recommendations. Show each available signal, its weighted contribution, reasons, sources, effective weights, and candidate funnel. Demo profiles/interactions are synthetic and labeled as such.
5. **TWSMA:** Open TWSMA Analytics. Explain that the pipeline analyzes music-news RSS, not social-media posts. Show article links, source names, sentiment counts, keywords, artist mentions, and publication dates separately from retrieval times.

## Local content recommendation explanation

The browser makes TF-IDF vectors from available title, artist, album, and genre terms. Cosine similarity ranks local files. For multiple liked songs, it averages the candidate's pairwise cosine similarities to those liked tracks. Displayed matching features come from the metadata; missing information is shown as Unknown and tracks without a usable similarity are not assigned an invented score.

## Backend hybrid recommendation explanation

The FastAPI engine combines content, collaborative, trend, and TWSMA text signals. For each track, only available component signals contribute; their configured weights are renormalized to sum to one. The trace records the formula, effective weights, evidence, reasons, data sources, candidate flow, and score components. Catalogue metadata recommendations do not depend on audio playback eligibility.

## TWSMA explanation

Configured RSS articles are fetched and deduplicated by URL. The service strips markup, tokenizes text, removes stopwords, and runs VADER sentiment. It summarizes sentiment labels, keyword counts, catalogue artist mentions, and sentiment counts by publication date when dates exist. Publication time and retrieval time are independent fields.

## Limitations to disclose

- Embedded ID3 tag extraction is implemented for MP3. Other formats use filename parsing and browser-provided duration.
- Recommendations need overlapping metadata. A song with too little information may not receive a similarity score.
- The backend does not receive local files. Its hybrid engine works on catalogue tracks and demo interactions.
- Live MusicBrainz, Last.fm, and RSS results depend on network access, provider availability, and API/feed configuration.
- Last.fm chart data requires `LASTFM_API_KEY`; MusicBrainz search is not a chart or popularity ranking.
