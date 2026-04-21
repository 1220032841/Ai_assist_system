@echo off
title AI Assist System - Local One Click Start
cd /d "%~dp0"
powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0start_local_online.ps1"
exit /b
