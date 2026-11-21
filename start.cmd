@echo off
docker start focus-lab2-mongodb >nul
if errorlevel 1 (
    echo MongoDB could not start. Open Docker Desktop and try again.
    exit /b 1
)
wsl.exe -d Ubuntu -u root --cd "%~dp0" -- bash deploy/start.sh
if errorlevel 1 (
    echo Startup failed. See the message above.
    exit /b 1
)
