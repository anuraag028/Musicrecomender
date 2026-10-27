# Music Recommender — Recommended Systems + TWSMA

A small local web app for a college viva. It combines content-based filtering, collaborative filtering, real catalogue/chart metadata when available, and a simple TWSMA music-news analysis module. The interface is intentionally minimal: search, generate a playlist, view trending tracks, and play music in the app using an embedded YouTube player.

## Requirements
- Windows 10/11
- Python 3.11+
- Node.js LTS + npm
- Internet access for external music sources

## Run on Windows

Open PowerShell in this folder.

### 1. Configure backend
```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Optional keys in `.env`:
- `LASTFM_API_KEY` enables Last.fm chart data.
- `YOUTUBE_API_KEY` enables YouTube Data API search for candidate videos.
- MusicBrainz is used for catalogue/release metadata and should be accessed respectfully with a descriptive User-Agent.

Do not commit `.env` or share API keys.

### 2. Start backend
In the project root:
```powershell
python backend/run_backend.py
```
Backend: http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs

### 3. Start frontend
Open a second PowerShell terminal:
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Frontend: http://127.0.0.1:5173

### 4. Populate real catalogue data
Click **Sync real music** in the app. This asks the backend to retrieve real provider data. Provider rate limits, network availability and API credentials affect the results. If the list remains empty, open `/api/diagnostics/providers` and `/docs` to inspect status. The app intentionally does not fill an empty catalogue with invented songs.

## Playback
Click **Play** beside a song. The embedded player appears in the app; playback is provided by YouTube's embed player/search embed. This is not a direct audio stream, and availability depends on YouTube, region and embedding restrictions. Use the actual play control in the embedded player. The app does not download or redistribute music.

## What can be simulated?
The three demo user profiles and their initial preferences/interactions are explicitly synthetic. Song and release records must come from external providers. Trend and TWSMA signals can be unavailable when providers cannot be reached; unavailable signals should not be presented as real data.

## Viva flow
1. Select a demo listener.
2. Generate the playlist.
3. Explain content-based and collaborative scores in the backend trace/API docs.
4. Click a track and demonstrate in-app playback.
5. Show trending catalogue data and explain the source/provenance.
6. Explain the TWSMA module and be honest about provider/API limitations.

## Tests
```powershell
python -m compileall -q backend
python -m pytest backend/tests -v
```
Run the frontend production build with `npm run build` inside `frontend`.
