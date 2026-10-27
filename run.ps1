Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting Social-Aware Hybrid Music Recommender..." -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Start Backend
Write-Host "Starting Backend API on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python backend/run_backend.py"

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "Starting Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host ""
Write-Host "Servers launched in separate PowerShell windows!" -ForegroundColor Yellow
Write-Host "Frontend:        http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "Backend API:     http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Interactive Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
