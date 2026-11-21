@echo off
wsl.exe -d Ubuntu -u root --cd "%~dp0" -- bash deploy/start.sh
if errorlevel 1 (
    echo Startup failed. See the message above.
    exit /b 1
)
