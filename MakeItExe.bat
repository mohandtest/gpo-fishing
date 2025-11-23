@echo off
echo ========================================
echo  GPO Fishing Macro - Simple Build Script
echo ========================================
echo.

REM Install all requirements first
echo [1/5] Installing requirements...
python -m pip install -r requirements.txt

REM Fix numpy installation issues
echo [2/5] Fixing numpy installation...
python -m pip uninstall numpy -y
python -m pip install numpy==2.3.5

REM Install PyInstaller if not present
echo [3/5] Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM Convert icon
echo [4/5] Converting icon...
python -c "from PIL import Image; img = Image.open('images/icon.webp').convert('RGBA'); img.save('icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])" 2>nul
if errorlevel 1 (
    echo Warning: Could not convert icon, building without icon...
    set ICON_PARAM=
) else (
    set ICON_PARAM=--icon=icon.ico
)

REM Clean previous builds
echo [5/5] Cleaning previous builds...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist *.spec del *.spec >nul 2>&1

REM Build executable
echo Building executable...
echo This may take several minutes...
echo.

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "GPO_Fishing_Macro" ^
    %ICON_PARAM% ^
    --add-data "images;images" ^
    --add-data "src;src" ^
    --paths=src ^
    --exclude-module=numpy._core._exceptions ^
    --exclude-module=numpy.core ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    --hidden-import=customtkinter ^
    --hidden-import=pystray ^
    --hidden-import=win32api ^
    --hidden-import=win32con ^
    --hidden-import=mss ^
    --hidden-import=keyboard ^
    --hidden-import=pynput ^
    --hidden-import=pkg_resources ^
    --hidden-import=importlib_metadata ^
    --hidden-import=platformdirs ^
    --hidden-import=zipp ^
    --hidden-import=jaraco ^
    --hidden-import=jaraco.text ^
    --hidden-import=jaraco.context ^
    --hidden-import=jaraco.functools ^
    --hidden-import=gui ^
    --hidden-import=settings ^
    --hidden-import=themes ^
    --hidden-import=updater ^
    --hidden-import=utils ^
    --collect-all=customtkinter ^
    --collect-all=pystray ^
    --collect-all=jaraco ^
    --collect-all=platformdirs ^
    --collect-all=numpy ^
    --distpath=dist ^
    --workpath=build ^
    --specpath=. ^
    src/main.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    echo.
    echo Try these solutions:
    echo 1. Run as administrator
    echo 2. python -m pip install --upgrade pyinstaller
    echo 3. Delete build/ and dist/ folders and try again
    echo.
    pause
    exit /b 1
)

REM Clean up
if exist icon.ico del icon.ico >nul 2>&1
if exist GPO_Fishing_Macro.spec del GPO_Fishing_Macro.spec >nul 2>&1

echo.
echo ========================================
echo  BUILD SUCCESS!
echo  Output: dist\GPO_Fishing_Macro.exe
echo ========================================
echo.
pause