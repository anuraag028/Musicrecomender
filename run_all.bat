@echo off
echo ===================================================
echo Starting Social-Aware Hybrid Music Recommender
echo ===================================================

echo Starting Backend API Server (FastAPI on http://127.0.0.1:8000)...
start "Music Recommender - Backend" cmd /k "python backend\run_backend.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server (Vite on http://127.0.0.1:5173)...
start "Music Recommender - Frontend" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo Both servers started!
echo Frontend: http://127.0.0.1:5173
echo Backend API Docs: http://127.0.0.1:8000/docs
echo ===================================================
pause
