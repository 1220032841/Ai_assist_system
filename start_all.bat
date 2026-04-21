@echo off
title AI Teaching System Launcher
echo ===================================================
echo       AI Teaching System - One-Click Start
echo ===================================================
echo.

:: 1. Check Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is NOT running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b
)

echo [INFO] Docker is running.
echo.

:: 2. Start Backend (in a new window)
echo [1/3] Starting Backend Services (Docker)...
start "Backend Services" cmd /k "powershell -ExecutionPolicy Bypass -File deploy.ps1"

:: 3. Wait a bit for backend to initialize
echo [2/3] Waiting for backend to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

:: 4. Start Frontend (in a new window)
echo [3/3] Starting Frontend...
start "Frontend" cmd /k "call run_frontend.bat"

echo.
echo ===================================================
echo       System Started!
echo ===================================================
echo.
echo Backend API: http://localhost:8000/docs
echo Frontend UI: http://localhost:5173
echo.
echo You can close this window, but keep the other two windows open.
pause
