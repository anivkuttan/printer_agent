REM Load .env variables manually
for /f "tokens=1,* delims==" %%A in ('type .env') do (
    if not "%%A"=="" set %%A=%%B
)

REM Use the env variable
if exist "%INNO_COMPILER_PATH%" (
    set INNO_COMPILER="%INNO_COMPILER_PATH%"
) else (
    REM fallback
    set INNO_COMPILER="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

@echo off
cls
echo ==============================
echo Building Laundry Printer Agent
echo ==============================


set AGENT_NAME=laundry_printer_agent_2.0.3
set INSTALLER_NAME=LAUNDRYPrinterAgentInstaller.exe
set MAIN_FILE=src\app.py
set VENV=.venv
 
echo Activating virtual environment...
call %VENV%\Scripts\activate.bat

echo Installing PyInstaller (silent)...
pip install pyinstaller >nul 2>&1

echo Building executable with PyInstaller...
@REM pyinstaller --onefile --noconsole --name %AGENT_NAME% %MAIN_FILE%
pyinstaller --onefile --noconsole --paths src --name %AGENT_NAME% %MAIN_FILE%

echo Creating installer with Inno Setup...
%INNO_COMPILER% printer_agent.iss

echo.
echo Build complete!
echo ------------------------------
echo  EXE:       dist\%AGENT_NAME%.exe
echo  Installer: dist\%INSTALLER_NAME%
echo ------------------------------
echo Done!

