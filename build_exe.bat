@echo off
REM Build script for GLaDOS Game Launcher
REM This script automates the process of building the executable

echo Building GLaDOS Game Launcher executable...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Error: Virtual environment not found!
    echo Please create a virtual environment first with: python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment and build
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing/updating PyInstaller...
python -m pip install --upgrade pyinstaller

echo Cleaning previous build...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo Building executable...
python -m PyInstaller --clean glados_launcher.spec

if exist "dist\GLaDOS_Game_Launcher.exe" (
    echo.
    echo =====================================================
    echo Build completed successfully!
    echo Executable location: dist\GLaDOS_Game_Launcher.exe
    for %%A in (dist\GLaDOS_Game_Launcher.exe) do echo File size: %%~zA bytes
    echo =====================================================
    echo.
) else (
    echo.
    echo =====================================================
    echo Build failed! Please check the error messages above.
    echo =====================================================
    echo.
)

pause