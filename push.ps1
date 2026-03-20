# MindPeek Git Push Script
cd "c:\Users\Administrator\Desktop\perMIR"

Write-Host "=== Git Push Script for MindPeek ===" -ForegroundColor Cyan

# Check if git repo exists
if (!(Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit: MindPeek - LLM user profiling system"
} else {
    Write-Host "Git repo exists, adding and committing..." -ForegroundColor Yellow
    git add .
    git commit -m "Update: MindPeek - LLM user profiling system"
}

# Set remote
git branch -M main
git remote remove origin 2>$null
git remote add origin https://github.com/GRright/MindPeek.git

Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host "=== Done ===" -ForegroundColor Green
