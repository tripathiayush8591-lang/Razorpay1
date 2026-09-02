# Agentic Commerce - Local Development Launcher
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting Agentic Commerce (Frontend + Backend)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Launch FastAPI Backend
Write-Host "Launching FastAPI backend on http://127.0.0.1:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python app/main.py"

# 2. Launch Vite React Frontend
Write-Host "Launching Vite React frontend on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host "`nBoth services have been launched in separate PowerShell windows!" -ForegroundColor Yellow
Write-Host "  -> Storefront UI:       http://localhost:5173" -ForegroundColor White
Write-Host "  -> Admin Portal:        http://localhost:5173/admin" -ForegroundColor White
Write-Host "  -> Backend API:         http://127.0.0.1:8000" -ForegroundColor White
Write-Host "  -> Interactive Docs:    http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "`nDemo Admin Credentials:" -ForegroundColor Yellow
Write-Host "  Email:    admin@runcraft.internal" -ForegroundColor White
Write-Host "  Password: demosecret123`n" -ForegroundColor White
