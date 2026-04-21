@echo off
title AI Assist System - Local Stop
setlocal

cd /d "%~dp0"

echo ===================================================
echo   AI Assist System - Local Stop
echo ===================================================
echo.

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker command not found.
    pause
    exit /b 1
)

docker compose -f docker-compose.online.yml --env-file .env.online down
if %errorlevel% neq 0 (
    echo [ERROR] Failed to stop services.
    pause
    exit /b 1
)

echo [OK] Services stopped.
pause
exit /b 0
