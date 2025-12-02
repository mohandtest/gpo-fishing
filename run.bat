@echo off
cd /d "%~dp0"

REM Check Python 3.14+ not supported
py -3 -c "import sys; exit(1 if sys.version_info >= (3, 14) else 0)" 2>nul
if errorlevel 1 exit /b 1

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat

REM Run silently using py launcher
start "" pyw -3 src/main.py