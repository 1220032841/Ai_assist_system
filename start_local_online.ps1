Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  AI Assist System - Local One Click Start" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker command not found." -ForegroundColor Red
    Write-Host "Please install Docker Desktop first." -ForegroundColor Yellow
    return
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running." -ForegroundColor Red
    Write-Host "Please start Docker Desktop, then run this script again." -ForegroundColor Yellow
    return
}

if (-not (Test-Path ".env.online")) {
    Write-Host "[WARN] .env.online not found. Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.online.example" ".env.online"
    Write-Host "[WARN] Please edit .env.online (SECRET_KEY / DB password / LLM_API_KEY), then run again." -ForegroundColor Yellow
    Start-Process notepad ".env.online"
    return
}

Write-Host "[INFO] Starting containers and running migrations..." -ForegroundColor Green
& "$PSScriptRoot\deploy_online.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Startup failed. Please check output above." -ForegroundColor Red
    return
}

Write-Host "[INFO] Waiting for health check..." -ForegroundColor Green
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1/api/v1/openapi.json" -TimeoutSec 3
        if ($resp.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    }
    catch {
        # Keep retrying while containers warm up.
    }
    Start-Sleep -Seconds 1
}

if (-not $healthy) {
    Write-Host "[WARN] Service health check timed out, but containers may still be starting." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[OK] Local service should be available now." -ForegroundColor Green
Write-Host "[OK] Open: http://127.0.0.1/" -ForegroundColor Green
Write-Host "[TIP] In Sakura FRP, set local IP 127.0.0.1 and local port 80." -ForegroundColor Cyan
Write-Host ""
Start-Process "http://127.0.0.1/"
