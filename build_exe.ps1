# PowerShell Build script for GLaDOS Game Launcher
# This script automates the process of building the executable

Write-Host "Building GLaDOS Game Launcher executable..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first with: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Set up paths
$venvPython = ".\.venv\Scripts\python.exe"

Write-Host "Installing/updating PyInstaller..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pyinstaller

Write-Host "Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}

Write-Host "Building executable..." -ForegroundColor Yellow
& $venvPython -m PyInstaller --clean glados_launcher.spec

if (Test-Path "dist\GLaDOS_Game_Launcher.exe") {
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Executable location: dist\GLaDOS_Game_Launcher.exe" -ForegroundColor Green
    $fileSize = (Get-Item "dist\GLaDOS_Game_Launcher.exe").Length
    Write-Host "File size: $([math]::Round($fileSize / 1MB, 2)) MB ($fileSize bytes)" -ForegroundColor Green
    Write-Host "=====================================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=====================================================" -ForegroundColor Red
    Write-Host "Build failed! Please check the error messages above." -ForegroundColor Red
    Write-Host "=====================================================" -ForegroundColor Red
    Write-Host ""
}

Read-Host "Press Enter to exit"