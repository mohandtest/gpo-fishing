@echo off
echo ========================================
echo   GPO Autofish - Easy Installation
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found

echo.
echo [2/4] Upgrading pip to latest version...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not upgrade pip, continuing anyway...
) else (
    echo ✓ Pip upgraded successfully
)

echo.
echo [3/4] Installing required packages...
echo Installing core dependencies...
echo This may take a few minutes...
pip install -r requirements.txt --no-warn-script-location
if errorlevel 1 (
    echo ERROR: Failed to install packages from requirements.txt
    echo.
    echo Trying alternative installation method...
    echo Installing packages individually...
    python -m pip install customtkinter --no-warn-script-location
    python -m pip install darkdetect --no-warn-script-location
    python -m pip install keyboard --no-warn-script-location
    python -m pip install mss --no-warn-script-location
    python -m pip install numpy --no-warn-script-location
    python -m pip install packaging --no-warn-script-location
    python -m pip install pillow --no-warn-script-location
    python -m pip install pynput --no-warn-script-location
    python -m pip install pyinstaller --no-warn-script-location
    python -m pip install pywin32 --no-warn-script-location
    python -m pip install pystray --no-warn-script-location
    python -m pip install six --no-warn-script-location
    
    if errorlevel 1 (
        echo ERROR: Installation failed completely
        echo.
        echo Possible solutions:
        echo 1. Run as administrator
        echo 2. Check your internet connection
        echo 3. Update Python to latest version
        echo 4. Try: python -m pip install --user [package_name]
        echo.
        pause
        exit /b 1
    )
)
echo ✓ Packages installed successfully

echo.
echo [4/4] Verifying installation...
python -c "import keyboard, pynput, mss, numpy, PIL; print('✓ Core modules verified')" 2>nul
if errorlevel 1 (
    echo WARNING: Some core modules may not be properly installed
    echo The program may still work, but some features might be limited
)

python -c "import customtkinter, pystray; print('✓ UI modules verified')" 2>nul
if errorlevel 1 (
    echo NOTE: UI modules may have issues - try running as administrator
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo To run GPO Autofish:
echo   • Double-click "run.bat" (recommended)
echo   • Or run "python src/main.py" in command prompt
echo.
echo Features available:
echo   ✓ Auto-fishing with PD controller
echo   ✓ Auto-purchase system
echo   ✓ Discord webhook notifications
echo   ✓ System tray support
echo   ✓ Auto-recovery system
echo   ✓ Pause/Resume functionality
echo.
echo Press any key to exit...
pause >nul