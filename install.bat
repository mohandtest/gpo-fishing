@echo off
setlocal enabledelayedexpansion
echo ========================================
echo   GPO Autofish - Easy Installation
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.12 or 3.13 from https://python.org
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
echo Installing packages individually...
echo This may take several minutes...
echo.

set FAILED_PACKAGES=
set FAILED_COUNT=0

echo Installing customtkinter...
python -m pip install customtkinter >nul 2>&1
if errorlevel 1 (
    echo ✗ customtkinter failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! customtkinter
    set /a FAILED_COUNT+=1
) else (
    echo ✓ customtkinter installed
)

echo Installing darkdetect...
python -m pip install darkdetect >nul 2>&1
if errorlevel 1 (
    echo ✗ darkdetect failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! darkdetect
    set /a FAILED_COUNT+=1
) else (
    echo ✓ darkdetect installed
)

echo Installing keyboard...
python -m pip install keyboard >nul 2>&1
if errorlevel 1 (
    echo ✗ keyboard failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! keyboard
    set /a FAILED_COUNT+=1
) else (
    echo ✓ keyboard installed
)

echo Installing mss...
python -m pip install mss >nul 2>&1
if errorlevel 1 (
    echo ✗ mss failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! mss
    set /a FAILED_COUNT+=1
) else (
    echo ✓ mss installed
)

echo Installing numpy...
python -m pip install numpy >nul 2>&1
if errorlevel 1 (
    echo ✗ numpy failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! numpy
    set /a FAILED_COUNT+=1
) else (
    echo ✓ numpy installed
)

echo Installing pillow...
python -m pip install pillow >nul 2>&1
if errorlevel 1 (
    echo ✗ pillow failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! pillow
    set /a FAILED_COUNT+=1
) else (
    echo ✓ pillow installed
)

echo Installing pynput...
python -m pip install pynput >nul 2>&1
if errorlevel 1 (
    echo ✗ pynput failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! pynput
    set /a FAILED_COUNT+=1
) else (
    echo ✓ pynput installed
)

echo Installing pywin32...
python -m pip install pywin32 >nul 2>&1
if errorlevel 1 (
    echo ✗ pywin32 failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! pywin32
    set /a FAILED_COUNT+=1
) else (
    echo ✓ pywin32 installed
)

echo Installing pystray...
python -m pip install pystray >nul 2>&1
if errorlevel 1 (
    echo ✗ pystray failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! pystray
    set /a FAILED_COUNT+=1
) else (
    echo ✓ pystray installed
)

echo Installing requests...
python -m pip install requests >nul 2>&1
if errorlevel 1 (
    echo ✗ requests failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! requests
    set /a FAILED_COUNT+=1
) else (
    echo ✓ requests installed
)

echo Installing opencv-python...
python -m pip install opencv-python >nul 2>&1
if errorlevel 1 (
    echo ✗ opencv-python failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! opencv-python
    set /a FAILED_COUNT+=1
) else (
    echo ✓ opencv-python installed
)

echo Installing easyocr ^(this may take a while - 1GB+ download^)...
python -m pip install easyocr >nul 2>&1
if errorlevel 1 (
    echo ✗ easyocr failed
    set FAILED_PACKAGES=!FAILED_PACKAGES! easyocr
    set /a FAILED_COUNT+=1
) else (
    echo ✓ easyocr installed
)

echo.
if !FAILED_COUNT! GTR 0 (
    echo ⚠️ WARNING: !FAILED_COUNT! package^(s^) failed to install
    echo.
    echo Failed packages:!FAILED_PACKAGES!
    echo.
    echo TO FIX:
    echo 1. Make sure you're using Python 3.12 or 3.13 ^(NOT 3.14+^)
    echo 2. Try running install.bat as Administrator
    echo 3. Check your internet connection
    echo 4. Install manually: python -m pip install [package_name]
    echo.
) else (
    echo ✓ All packages installed successfully!
)

echo.
echo [4/4] Verifying installation...
python -c "import keyboard, pynput, mss, numpy, PIL; print('✓ Core modules verified')" 2>nul
if errorlevel 1 (
    echo WARNING: Some core modules may not be properly installed
    echo The program may still work, but some features might be limited
)

python -c "import customtkinter, pystray; print('✓ UI modules verified')" 2>nul
if errorlevel 1 (
    echo NOTE: UI modules may have issues - try asking in our discord!
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
echo Press any key to exit...
pause >nul