@echo off
setlocal enabledelayedexpansion

cls
echo ===============================================
echo     Building LAUNDRY PRINTER AGENT (Windows)
echo ===============================================

REM ----------------------------------------
REM Load .env variables if exists
REM ----------------------------------------
if exist ".env" (
    for /f "tokens=1,* delims==" %%A in ('type .env') do (
        if not "%%A"=="" set %%A=%%B
    )
)

REM ----------------------------------------
REM Detect Inno Setup (from env or fallback)
REM ----------------------------------------
if defined INNO_COMPILER_PATH (
    set INNO_COMPILER="%INNO_COMPILER_PATH%"
) else (
    set INNO_COMPILER="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

echo Using Inno Compiler: %INNO_COMPILER%
echo.

REM ----------------------------------------
REM Extract version from ISS file
REM ----------------------------------------
for /f "tokens=2 delims==" %%V in ('findstr /b "AppVersion" printer_agent.iss') do (
    set APP_VERSION=%%V
)

echo Detected Version: %APP_VERSION%
echo.

REM ----------------------------------------
REM Define dynamic names
REM ----------------------------------------
set AGENT_NAME=laundry_printer_agent_%APP_VERSION%
set INSTALLER_NAME=Laundry_Printer_Agent_Installer-%APP_VERSION%.exe
set MAIN_FILE=src\app.py
set VENV=.venv

REM ----------------------------------------
REM Cleanup old build
REM ----------------------------------------
echo Cleaning old build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
del /q *.spec 2>nul
echo Done.
echo.

REM ----------------------------------------
REM Activate virtual environment
REM ----------------------------------------
echo Activating virtual environment...
call %VENV%\Scripts\activate.bat
echo.

REM ----------------------------------------
REM Install PyInstaller
REM ----------------------------------------
echo Installing PyInstaller silently...
pip install pyinstaller >nul 2>&1
echo Done.
echo.

REM ----------------------------------------
REM Build binary
REM ----------------------------------------
echo Building EXE with PyInstaller...
pyinstaller --onefile --noconsole --paths src --name %AGENT_NAME% %MAIN_FILE%
echo PyInstaller build completed.
echo.

REM ----------------------------------------
REM Create installer
REM ----------------------------------------
echo Creating installer using Inno Setup...
%INNO_COMPILER% printer_agent.iss
echo Installer build completed.
echo.

REM ----------------------------------------
REM Summary
REM ----------------------------------------
echo ==============================================
echo Build Completed Successfully!
echo ----------------------------------------------
echo EXE:       dist\%AGENT_NAME%.exe
echo Installer: dist\%INSTALLER_NAME%
echo ==============================================
echo Done!
echo.

pause
