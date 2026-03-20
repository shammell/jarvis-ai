# Quick Start Script for JARVIS Web App

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JARVIS Web App - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env with Supabase credentials" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Required variables:" -ForegroundColor Yellow
    Write-Host "  SUPABASE_URL=your_url" -ForegroundColor Gray
    Write-Host "  SUPABASE_SERVICE_KEY=your_key" -ForegroundColor Gray
    Write-Host "  SUPABASE_JWT_SECRET=your_secret" -ForegroundColor Gray
    Write-Host "  CORS_ORIGINS=http://localhost:3000" -ForegroundColor Gray
    exit 1
}

# Check if web/.env.local exists
if (-not (Test-Path "web\.env.local")) {
    Write-Host "WARNING: web/.env.local not found!" -ForegroundColor Yellow
    Write-Host "Creating from example..." -ForegroundColor Yellow
    Copy-Item "web\.env.local.example" "web\.env.local"
    Write-Host "Please edit web/.env.local with your Supabase credentials" -ForegroundColor Yellow
    Write-Host ""
}

# Install backend dependencies
Write-Host "Installing backend dependencies..." -ForegroundColor Green
pip install supabase pyjwt

# Install frontend dependencies
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Green
Set-Location web
npm install
Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run database migrations in Supabase SQL Editor" -ForegroundColor White
Write-Host "   File: supabase/migrations/20260309_create_chat_tables.sql" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start backend (Terminal 1):" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start frontend (Terminal 2):" -ForegroundColor White
Write-Host "   cd web && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Open http://localhost:3000" -ForegroundColor White
Write-Host ""
