# JARVIS MVP Launcher (Windows)
# Starts API backend + lightweight MVP frontend for quick testing and sharing.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JARVIS MVP Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] .env file not found. Copy from .env.example first." -ForegroundColor Red
    exit 1
}

$envRaw = Get-Content ".env" -Raw
if ($envRaw -match "GROQ_API_KEY=your_groq_api_key_here") {
    Write-Host "[ERROR] GROQ_API_KEY is still placeholder in .env" -ForegroundColor Red
    exit 1
}

# Ensure logs and MVP folder exist
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
if (-not (Test-Path "mvp\index.html")) {
    Write-Host "[ERROR] mvp/index.html not found" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Starting JARVIS API on http://localhost:8000" -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python main.py"

Start-Sleep -Seconds 5

Write-Host "[2/3] Checking API health" -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 8
    if ($health.StatusCode -ne 200) {
        Write-Host "[WARN] API health returned status $($health.StatusCode)" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] API healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARN] API health check failed. API may still be starting." -ForegroundColor Yellow
}

Write-Host "[3/3] Starting MVP frontend on http://localhost:8081" -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m http.server 8081 --directory mvp"

Write-Host "" 
Write-Host "MVP running:" -ForegroundColor Green
Write-Host "- API: http://localhost:8000" -ForegroundColor White
Write-Host "- API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "- MVP UI: http://localhost:8081" -ForegroundColor White
Write-Host "" 
Write-Host "To share with friend, run one tunnel command in a new terminal:" -ForegroundColor Cyan
Write-Host "- cloudflared tunnel --url http://localhost:8081" -ForegroundColor Gray
Write-Host "- or: ngrok http 8081" -ForegroundColor Gray
Write-Host "" 
Write-Host "Close spawned PowerShell windows to stop MVP." -ForegroundColor Yellow
