@echo off
title GitHub Auto Updater
color 0A

:: Configure Git credentials
git config --global user.name "far9ouch"
git config --global user.email "far9ouch07@gmail.com"

:loop
cls
echo GitHub Auto Updater Running...
echo Repository: https://github.com/far9ouch/spotifyworkwithAPI
echo.
echo Last check: %date% %time%
echo.

:: Remove existing git repository
if exist .git (
    echo Cleaning Git folder...
    rmdir /s /q .git
)

:: Initialize repository
echo Initializing Git...
git init >nul

:: Add all files
echo Checking for changes...
git add . >nul

:: Create commit
echo Creating new commit...
git commit -m "Auto update: %date% %time%" >nul

:: Set up remote
echo Setting up remote...
git remote add origin https://github.com/far9ouch/spotifyworkwithAPI.git >nul

:: Switch to main branch
echo Switching to main branch...
git branch -M main >nul

:: Push changes
echo Pushing to GitHub...
git push -f origin main >nul

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Repository updated successfully!
) else (
    echo.
    echo [ERROR] Update failed. Will retry in next cycle.
)

echo.
echo Waiting 5 minutes before next update...
echo Press Ctrl+C to stop auto-updating.
echo.

:: Wait 5 minutes before next update
timeout /t 300 /nobreak >nul
goto loop 