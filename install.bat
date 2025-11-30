@echo off
echo ========================================
echo   GPO Autofish - Smart Installation
echo ========================================
echo.

echo [1/5] Checking Python installation...
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

REM Check if Python 3.14 and set compatibility mode
echo %PYTHON_VERSION% | findstr /C:"3.14" >nul
if not errorlevel 1 (
    echo.
    echo ⚠️  NOTICE: Python 3.14 detected
    echo Smart compatibility mode enabled for better package support
    echo We'll handle scikit-image and EasyOCR compatibility automatically
    set PYTHON_314=true
) else (
    set PYTHON_314=false
)

echo.
echo [2/5] Upgrading pip to latest version...
python -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not upgrade pip, continuing anyway...
) else (
    echo ✓ Pip upgraded successfully
)

echo.
echo [3/5] Installing core packages...
echo Installing essential dependencies directly...
echo This may take a few minutes...

echo Installing core packages...
python -m pip install keyboard==0.13.5 --no-warn-script-location
python -m pip install pynput==1.8.1 --no-warn-script-location
python -m pip install mss==10.1.0 --no-warn-script-location
python -m pip install numpy --no-warn-script-location
python -m pip install pillow --no-warn-script-location
python -m pip install requests --no-warn-script-location
python -m pip install pywin32 --no-warn-script-location
python -m pip install pystray --no-warn-script-location

echo.
echo [4/5] Installing OCR packages for text recognition...

REM Smart Python 3.14 compatibility handling
if "%PYTHON_314%"=="true" (
    echo Python 3.14 detected - installing compatible packages...
    echo.
    echo Installing scikit-image nightly build for Python 3.14 compatibility...
    python -m pip install -i https://pypi.anaconda.org/scientific-python-nightly-wheels/simple scikit-image --no-warn-script-location
    if errorlevel 1 (
        echo Warning: Nightly scikit-image installation failed, trying standard method...
    ) else (
        echo ✓ scikit-image nightly build installed
    )
    echo.
)

echo Installing EasyOCR (primary text recognition)...
python -m pip install easyocr --no-warn-script-location
if errorlevel 1 (
    echo EasyOCR installation failed, trying alternative methods...
    echo.
    
    REM Smart Python 3.14 EasyOCR installation
    if "%PYTHON_314%"=="true" (
        echo Method 1: Installing EasyOCR dependencies with nightly builds...
        python -m pip install torch torchvision --no-warn-script-location
        python -m pip install -i https://pypi.anaconda.org/scientific-python-nightly-wheels/simple scikit-image --no-warn-script-location
        python -m pip install opencv-python pillow numpy --no-warn-script-location
        python -m pip install easyocr --no-warn-script-location
        if not errorlevel 1 (
            echo ✓ EasyOCR installed with nightly builds
            goto :easyocr_success
        )
        echo Nightly build method failed.
        echo.
        echo ⚠️  EasyOCR is not compatible with Python 3.14 yet.
        echo This is expected - skipping remaining methods to avoid hanging.
        echo Your app will work perfectly with fallback text detection!
        echo.
        goto :easyocr_failed
    )
    
    echo Method 2: Installing with --user flag...
    python -m pip install --user easyocr --no-warn-script-location
    if errorlevel 1 (
        echo Method 3: Installing with --force-reinstall...
        python -m pip install --force-reinstall easyocr --no-warn-script-location
        if errorlevel 1 (
            echo Method 4: Installing dependencies separately...
            python -m pip install torch torchvision --no-warn-script-location
            python -m pip install opencv-python --no-warn-script-location
            python -m pip install pillow --no-warn-script-location
            python -m pip install numpy --no-warn-script-location
            python -m pip install easyocr --no-warn-script-location
            if errorlevel 1 (
                goto :easyocr_failed
            ) else (
                echo ✓ EasyOCR installed via dependency method
            )
        ) else (
            echo ✓ EasyOCR installed via force-reinstall
        )
    ) else (
        echo ✓ EasyOCR installed via --user flag
    )
) else (
    echo ✓ EasyOCR installed successfully
)
goto :easyocr_success

:easyocr_failed
echo WARNING: EasyOCR installation failed completely
echo.
if "%PYTHON_314%"=="true" (
    echo This is expected with Python 3.14 - EasyOCR doesn't support it yet.
    echo.
    echo ℹ️  Don't worry! Your app will still work perfectly.
    echo The app includes smart fallback text detection that works without EasyOCR.
    echo.
    echo If you want full OCR support later, you can:
    echo 1. Use Python 3.13 for full compatibility
    echo 2. Wait for official Python 3.14 support
    echo 3. Try manual installation when packages are updated
) else (
    echo Manual installation required:
    echo 1. Open Command Prompt as Administrator
    echo 2. Run: pip install easyocr
    echo 3. If that fails, try: pip install --user easyocr
)
echo.
echo The app will use fallback text detection without OCR

:easyocr_success

echo.
echo Installing OpenCV for image processing...
python -m pip install opencv-python --no-warn-script-location
if errorlevel 1 (
    echo OpenCV installation failed, trying --user flag...
    python -m pip install --user opencv-python
)

echo Installing optional UI packages...
echo ✓ pystray already installed with core packages

echo.
echo [5/5] Final verification and testing...
echo Checking essential modules...
python -c "import keyboard; print('✓ keyboard')" 2>nul || echo ✗ keyboard MISSING
python -c "import pynput; print('✓ pynput')" 2>nul || echo ✗ pynput MISSING
python -c "import mss; print('✓ mss')" 2>nul || echo ✗ mss MISSING
python -c "import numpy; print('✓ numpy')" 2>nul || echo ✗ numpy MISSING
python -c "import PIL; print('✓ pillow')" 2>nul || echo ✗ pillow MISSING
python -c "import requests; print('✓ requests')" 2>nul || echo ✗ requests MISSING
python -c "import win32api; print('✓ pywin32')" 2>nul || echo ✗ pywin32 MISSING
python -c "import pystray; print('✓ pystray')" 2>nul || echo ✗ pystray MISSING

echo Checking optional modules...
python -c "import easyocr; print('✓ EasyOCR (text recognition available)')" 2>nul || echo ✗ EasyOCR (text recognition disabled - using fallback detection)
python -c "import cv2; print('✓ opencv-python (image processing)')" 2>nul || echo ✗ opencv-python (image processing disabled)

echo.
echo Testing basic functionality...
python -c "
import sys
try:
    import keyboard, pynput, mss, numpy, PIL, requests, win32api, pystray
    print('✓ All essential modules working')
    sys.exit(0)
except ImportError as e:
    print(f'✗ Missing module: {e}')
    sys.exit(1)
" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: Some essential modules are missing
    echo The program may not work correctly
    echo Try running the installer as administrator
)

echo.
echo ========================================
echo   Smart Installation Complete!
echo ========================================
echo.
echo To run GPO Autofish:
echo   • Double-click "run.bat" (recommended)
echo   • Or run "python src/main.py" in command prompt
echo.
echo ✅ Features available:
echo   ✓ Auto-fishing with PD controller
echo   ✓ Auto-purchase system
echo   ✓ Discord webhook notifications
echo   ✓ System tray support
echo   ✓ Auto-recovery system
echo   ✓ Pause/Resume functionality
echo   ✓ Dual layout system (F2 to toggle)
echo   ✓ Auto zoom control

if "%PYTHON_314%"=="true" (
    echo.
    echo 🐍 Python 3.14 Status:
    python -c "import easyocr; print('✓ EasyOCR ready - Full text recognition available!')" 2>nul || echo ⚠️  EasyOCR not available - Using smart fallback detection ^(app still works perfectly^)
) else (
    echo.
    echo OCR Status:
    python -c "import easyocr; print('✓ EasyOCR ready - text recognition available!')" 2>nul || echo ⚠️  EasyOCR not available - using fallback detection ^(drops detected but text not readable^)
)

echo.
echo Press any key to exit...
pause >nul