@echo off
cd frontend
echo Installing dependencies (if needed)...
call npm install
echo Starting Frontend Development Server...
call npm run dev
pause
