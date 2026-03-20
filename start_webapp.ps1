# JARVIS Web App - Start Script
# Starts both backend and frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting JARVIS Web App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Run setup_webapp.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Check if web/.env.local exists
if (-not (Test-Path "web\.env.local")) {
    Write-Host "ERROR: web/.env.local not found!" -ForegroundColor Red
    Write-Host "Run setup_webapp.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting backend on http://localhost:8000" -ForegroundColor Green
Write-Host "Starting frontend on http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host ""

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd web; npm run dev"

Write-Host ""
Write-Host "Both services started!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor White
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Close the PowerShell windows to stop the services" -ForegroundColor Yellow
