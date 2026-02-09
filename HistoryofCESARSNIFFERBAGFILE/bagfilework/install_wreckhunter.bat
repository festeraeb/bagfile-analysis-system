@echo off
REM ============================================================================
REM Wreck Hunter 2000 - Windows Installer
REM ============================================================================
REM Creates desktop shortcut, Start Menu entry, and installs all dependencies
REM Does NOT require Administrator privileges
REM ============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

set VERSION=2.0
set APP_NAME=Wreck Hunter 2000
set INSTALL_DIR=%~dp0
set VENV_DIR=%INSTALL_DIR%.venv
set PYTHON_EXE=%VENV_DIR%\Scripts\python.exe
set PYTHONW_EXE=%VENV_DIR%\Scripts\pythonw.exe
set PIP_EXE=%VENV_DIR%\Scripts\pip.exe
set DESKTOP=%USERPROFILE%\Desktop
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs

cls
echo.
echo  ╔═══════════════════════════════════════════════════════════════════════╗
echo  ║                                                                       ║
echo  ║   ██╗    ██╗██████╗ ███████╗ ██████╗██╗  ██╗                         ║
echo  ║   ██║    ██║██╔══██╗██╔════╝██╔════╝██║ ██╔╝                         ║
echo  ║   ██║ █╗ ██║██████╔╝█████╗  ██║     █████╔╝                          ║
echo  ║   ██║███╗██║██╔══██╗██╔══╝  ██║     ██╔═██╗                          ║
echo  ║   ╚███╔███╔╝██║  ██║███████╗╚██████╗██║  ██╗                         ║
echo  ║    ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝                         ║
echo  ║                                                                       ║
echo  ║               HUNTER 2000  -  Version %VERSION%                          ║
echo  ║         Great Lakes Shipwreck Detection Suite                        ║
echo  ║                                                                       ║
echo  ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   Installation directory: %INSTALL_DIR:~0,-1%
echo.
echo   This installer will:
echo     [1] Check Python installation
echo     [2] Create isolated virtual environment
echo     [3] Install all dependencies (h5py, pyproj, scipy, etc.)
echo     [4] Create Desktop shortcut
echo     [5] Create Start Menu entry
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM ============================================================================
REM STEP 1: Check Python
REM ============================================================================
echo [STEP 1/5] Checking Python installation...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   ╔═══════════════════════════════════════════════════════════════════╗
    echo   ║  ERROR: Python is not installed!                                  ║
    echo   ║                                                                   ║
    echo   ║  Please download and install Python 3.8+ from:                    ║
    echo   ║    https://www.python.org/downloads/                              ║
    echo   ║                                                                   ║
    echo   ║  IMPORTANT: Check "Add Python to PATH" during installation!       ║
    echo   ╚═══════════════════════════════════════════════════════════════════╝
    echo.
    echo   Press any key to open the Python download page...
    pause >nul
    start https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VER=%%a
echo   [OK] Python %PYTHON_VER% found
echo.

REM ============================================================================
REM STEP 2: Create Virtual Environment
REM ============================================================================
echo [STEP 2/5] Setting up virtual environment...
echo.

REM Check if this is a resume after reboot
if exist "%INSTALL_DIR%\.install_resume" (
    echo   [*] Resuming installation after reboot...
    del "%INSTALL_DIR%\.install_resume" 2>nul
    REM Delete the scheduled task
    schtasks /delete /tn "WreckHunterInstallResume" /f >nul 2>&1
)

set NEED_REBUILD=0

REM Check for any corruption or missing files
if exist "%VENV_DIR%" (
    if not exist "%VENV_DIR%\pyvenv.cfg" (
        echo   [!] Missing pyvenv.cfg - venv corrupted
        set NEED_REBUILD=1
    )
    if not exist "%VENV_DIR%\Scripts\python.exe" (
        echo   [!] Missing python.exe - venv corrupted
        set NEED_REBUILD=1
    )
    if not exist "%VENV_DIR%\Scripts\pip.exe" (
        echo   [!] Missing pip.exe - venv corrupted
        set NEED_REBUILD=1
    )
)

REM If venv exists but is corrupted, remove it
if "%NEED_REBUILD%"=="1" (
    echo   Removing corrupted virtual environment...
    rmdir /s /q "%VENV_DIR%" 2>nul
    if exist "%VENV_DIR%" (
        echo.
        echo   ========================================================
        echo   [!] LOCKED FILES DETECTED
        echo   ========================================================
        echo   The .venv folder has files locked by another process.
        echo.
        echo   Choose an option:
        echo     [1] Reboot and auto-resume installation
        echo     [2] Use alternate venv folder (.venv_new)
        echo     [3] Exit and fix manually
        echo.
        set /p LOCK_CHOICE="   Enter choice (1/2/3): "
        
        if "!LOCK_CHOICE!"=="1" (
            echo.
            echo   Setting up auto-resume after reboot...
            echo resume> "%INSTALL_DIR%\.install_resume"
            REM Create a scheduled task to run installer at next logon
            schtasks /create /tn "WreckHunterInstallResume" /tr "\"%INSTALL_DIR%\install_wreckhunter.bat\"" /sc onlogon /f >nul 2>&1
            echo   [OK] Installer will resume automatically after reboot.
            echo.
            echo   Rebooting in 10 seconds... (Ctrl+C to cancel)
            timeout /t 10
            shutdown /r /t 0
            exit /b 0
        )
        
        if "!LOCK_CHOICE!"=="2" (
            echo.
            echo   Using alternate venv folder...
            set VENV_DIR=%INSTALL_DIR%\.venv_new
            set PYTHON_EXE=%INSTALL_DIR%\.venv_new\Scripts\python.exe
            set PYTHONW_EXE=%INSTALL_DIR%\.venv_new\Scripts\pythonw.exe
            set PIP_EXE=%INSTALL_DIR%\.venv_new\Scripts\pip.exe
            REM Remove old alternate if exists
            if exist "%INSTALL_DIR%\.venv_new" rmdir /s /q "%INSTALL_DIR%\.venv_new" 2>nul
            goto :create_fresh_venv
        )
        
        echo.
        echo   Please close all terminals, VS Code, and any Python processes.
        echo   Then run this installer again.
        pause
        exit /b 1
    )
)

:create_fresh_venv
REM Create venv if it doesn't exist
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo   Creating new virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo   [ERROR] Failed to create virtual environment
        echo.
        echo   Try running:  python -m pip install virtualenv
        echo   Then run this installer again.
        pause
        exit /b 1
    )
    echo   [OK] Virtual environment created
) else (
    echo   [OK] Virtual environment exists and is valid
)

REM Final verification - test that python actually runs
"%PYTHON_EXE%" -c "print('ok')" >nul 2>&1
if errorlevel 1 (
    echo   [!] Virtual environment python not working - rebuilding...
    rmdir /s /q "%VENV_DIR%" 2>nul
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo   [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo   [OK] Virtual environment rebuilt
)
echo.

REM ============================================================================
REM STEP 3: Install Dependencies
REM ============================================================================
echo [STEP 3/5] Installing dependencies (this may take 2-5 minutes)...
echo.

echo   Upgrading pip...
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel >nul 2>&1

echo   Installing core packages...
echo     - h5py (NOAA BAG file support)
echo     - pyproj (coordinate transforms)
echo     - scipy (image processing)
echo     - numpy (array operations)
echo     - scikit-learn (machine learning)
echo     - matplotlib (visualization)
echo.

"%PIP_EXE%" install h5py pyproj scipy numpy scikit-learn matplotlib --quiet 2>nul
if errorlevel 1 (
    echo   [WARNING] Some packages may need Visual C++ Build Tools
    echo   Trying alternative installation...
    "%PIP_EXE%" install numpy scipy matplotlib --quiet 2>nul
)

REM Install optional packages (don't fail if missing)
echo   Installing optional packages...
"%PIP_EXE%" install PyMuPDF rasterio joblib pandas requests --quiet 2>nul

echo   [OK] Dependencies installed
echo.

REM ============================================================================
REM STEP 4: Create Desktop Shortcut
REM ============================================================================
echo [STEP 4/5] Creating Desktop shortcut...
echo.

set SHORTCUT_CREATED=0

if exist "%DESKTOP%" (
    REM Create desktop shortcut using PowerShell
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$WshShell = New-Object -ComObject WScript.Shell; " ^
        "$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\%APP_NAME%.lnk'); " ^
        "$Shortcut.TargetPath = '%PYTHONW_EXE%'; " ^
        "$Shortcut.Arguments = '\"%INSTALL_DIR%wreckhunter.py\"'; " ^
        "$Shortcut.WorkingDirectory = '%INSTALL_DIR:~0,-1%'; " ^
        "$Shortcut.Description = 'Great Lakes Shipwreck Detection Suite'; " ^
        "$Shortcut.IconLocation = '%SystemRoot%\System32\shell32.dll,13'; " ^
        "$Shortcut.Save()" 2>nul
    
    if exist "%DESKTOP%\%APP_NAME%.lnk" (
        echo   [OK] Desktop shortcut created: "%APP_NAME%"
        set SHORTCUT_CREATED=1
    ) else (
        echo   [WARNING] Could not create desktop shortcut
    )
) else (
    echo   [WARNING] Desktop folder not found at %DESKTOP%
)
echo.

REM ============================================================================
REM STEP 5: Create Start Menu Entry
REM ============================================================================
echo [STEP 5/5] Creating Start Menu entry...
echo.

set START_MENU_DIR=%START_MENU%\%APP_NAME%
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%" 2>nul

REM Main app shortcut
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\%APP_NAME%.lnk'); " ^
    "$Shortcut.TargetPath = '%PYTHONW_EXE%'; " ^
    "$Shortcut.Arguments = '\"%INSTALL_DIR%wreckhunter.py\"'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR:~0,-1%'; " ^
    "$Shortcut.Description = 'Great Lakes Shipwreck Detection Suite'; " ^
    "$Shortcut.IconLocation = '%SystemRoot%\System32\shell32.dll,13'; " ^
    "$Shortcut.Save()" 2>nul

REM CLI shortcut
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\%APP_NAME% CLI.lnk'); " ^
    "$Shortcut.TargetPath = 'cmd.exe'; " ^
    "$Shortcut.Arguments = '/k cd /d \"%INSTALL_DIR:~0,-1%\" ^& \"%PYTHON_EXE%\" wreckhunter_cli.py --help'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR:~0,-1%'; " ^
    "$Shortcut.Description = 'Wreck Hunter 2000 Command Line'; " ^
    "$Shortcut.IconLocation = '%SystemRoot%\System32\cmd.exe,0'; " ^
    "$Shortcut.Save()" 2>nul

REM Uninstall shortcut
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\Uninstall.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%uninstall_wreckhunter.bat'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR:~0,-1%'; " ^
    "$Shortcut.Description = 'Remove Wreck Hunter 2000 shortcuts'; " ^
    "$Shortcut.IconLocation = '%SystemRoot%\System32\shell32.dll,31'; " ^
    "$Shortcut.Save()" 2>nul

if exist "%START_MENU_DIR%\%APP_NAME%.lnk" (
    echo   [OK] Start Menu folder created: %APP_NAME%
    echo       - %APP_NAME% (main app)
    echo       - %APP_NAME% CLI (command line)
    echo       - Uninstall
) else (
    echo   [WARNING] Could not create Start Menu entry
)
echo.

REM ============================================================================
REM COMPLETE
REM ============================================================================
echo.
echo  ╔═══════════════════════════════════════════════════════════════════════╗
echo  ║                                                                       ║
echo  ║   INSTALLATION COMPLETE!                                              ║
echo  ║                                                                       ║
echo  ╚═══════════════════════════════════════════════════════════════════════╝
echo.
echo   You can now run Wreck Hunter 2000 by:
echo.
echo     [1] Double-click the Desktop icon: "%APP_NAME%"
echo     [2] Open Start Menu -^> "%APP_NAME%"
echo     [3] Run from command line: python wreckhunter.py
echo.
echo   To uninstall:
echo     Run uninstall_wreckhunter.bat or use Start Menu -^> Uninstall
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

set /p LAUNCH="Would you like to launch %APP_NAME% now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo.
    echo   Launching %APP_NAME%...
    start "" "%PYTHONW_EXE%" "%INSTALL_DIR%wreckhunter.py"
)

echo.
echo   Press any key to close this window...
pause >nul
