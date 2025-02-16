@echo off
echo Starting GitHub upload process...

:: Configure Git credentials
git config --global user.name "far9ouch"
git config --global user.email "far9ouch07@gmail.com"

:: Remove existing git repository if exists
if exist .git (
    echo Removing existing Git folder...
    rmdir /s /q .git
)

:: Initialize new repository
echo Creating fresh Git repository...
git init

:: Add all files
echo Adding files...
git add .

:: Create commit
echo Creating commit...
git commit -m "Update files"

:: Set up remote
echo Setting up remote...
git remote add origin https://github.com/far9ouch/spotifyworkwithAPI.git

:: Create and switch to main branch
echo Setting up main branch...
git branch -M main

:: Force push
echo Pushing to GitHub...
git push -f origin main

if %errorlevel% equ 0 (
    echo Upload successful!
) else (
    echo Upload failed. Please check your GitHub access.
    echo Make sure repository exists at: https://github.com/far9ouch/spotifyworkwithAPI
    pause
)

timeout /t 3 