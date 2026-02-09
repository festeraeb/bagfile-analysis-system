# ============================================================================
# Wreck Hunter 2000 - Windows Installer (PowerShell)
# ============================================================================
# Creates desktop shortcut, Start Menu entry, and installs all dependencies
# Does NOT require Administrator privileges
#
# Run: powershell -ExecutionPolicy RemoteSigned -File install_wreckhunter.ps1
# ============================================================================

param(
    [string]$InstallDir = (Get-Location).Path,
    [switch]$NoShortcuts,
    [switch]$Silent
)

$VERSION = "2.0"
$APP_NAME = "Wreck Hunter 2000"
$VENV_DIR = Join-Path $InstallDir ".venv"
$PYTHON_EXE = Join-Path $VENV_DIR "Scripts\python.exe"
$PYTHONW_EXE = Join-Path $VENV_DIR "Scripts\pythonw.exe"
$PIP_EXE = Join-Path $VENV_DIR "Scripts\pip.exe"

# Display banner
Clear-Host
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║                                                                       ║" -ForegroundColor Cyan
Write-Host "  ║   ██╗    ██╗██████╗ ███████╗ ██████╗██╗  ██╗                         ║" -ForegroundColor Cyan
Write-Host "  ║   ██║    ██║██╔══██╗██╔════╝██╔════╝██║ ██╔╝                         ║" -ForegroundColor Cyan
Write-Host "  ║   ██║ █╗ ██║██████╔╝█████╗  ██║     █████╔╝                          ║" -ForegroundColor Cyan
Write-Host "  ║   ██║███╗██║██╔══██╗██╔══╝  ██║     ██╔═██╗                          ║" -ForegroundColor Cyan
Write-Host "  ║   ╚███╔███╔╝██║  ██║███████╗╚██████╗██║  ██╗                         ║" -ForegroundColor Cyan
Write-Host "  ║    ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝                         ║" -ForegroundColor Cyan
Write-Host "  ║                                                                       ║" -ForegroundColor Cyan
Write-Host "  ║               HUNTER 2000  -  Version $VERSION                          ║" -ForegroundColor Cyan
Write-Host "  ║         Great Lakes Shipwreck Detection Suite                        ║" -ForegroundColor Cyan
Write-Host "  ║                                                                       ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Installation directory: $InstallDir" -ForegroundColor White
Write-Host ""
Write-Host "  This installer will:" -ForegroundColor Gray
Write-Host "    [1] Check Python installation" -ForegroundColor Gray
Write-Host "    [2] Create isolated virtual environment" -ForegroundColor Gray
Write-Host "    [3] Install all dependencies (h5py, pyproj, scipy, etc.)" -ForegroundColor Gray
Write-Host "    [4] Create Desktop shortcut" -ForegroundColor Gray
Write-Host "    [5] Create Start Menu entry" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""

# ============================================================================
# STEP 1: Check Python
# ============================================================================
Write-Host "[STEP 1/5] Checking Python installation..." -ForegroundColor Yellow
Write-Host ""
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "" -ForegroundColor Red
    Write-Host "  ╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "  ║  ERROR: Python is not installed!                                  ║" -ForegroundColor Red
    Write-Host "  ║                                                                   ║" -ForegroundColor Red
    Write-Host "  ║  Please download and install Python 3.8+ from:                    ║" -ForegroundColor Red
    Write-Host "  ║    https://www.python.org/downloads/                              ║" -ForegroundColor Red
    Write-Host "  ║                                                                   ║" -ForegroundColor Red
    Write-Host "  ║  IMPORTANT: Check 'Add Python to PATH' during installation!       ║" -ForegroundColor Red
    Write-Host "  ╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Start-Process "https://www.python.org/downloads/"
    exit 1
}
Write-Host ""

# ============================================================================
# STEP 2: Create Virtual Environment
# ============================================================================
Write-Host "[STEP 2/5] Setting up virtual environment..." -ForegroundColor Yellow
Write-Host ""

# Check if this is a resume after reboot
$resumeFile = Join-Path $INSTALL_DIR ".install_resume"
if (Test-Path $resumeFile) {
    Write-Host "  [*] Resuming installation after reboot..." -ForegroundColor Cyan
    Remove-Item $resumeFile -Force -ErrorAction SilentlyContinue
    # Remove the scheduled task
    schtasks /delete /tn "WreckHunterInstallResume" /f 2>&1 | Out-Null
}

$needRebuild = $false

# Check for any corruption or missing files
if (Test-Path $VENV_DIR) {
    if (-not (Test-Path (Join-Path $VENV_DIR "pyvenv.cfg"))) {
        Write-Host "  [!] Missing pyvenv.cfg - venv corrupted" -ForegroundColor Yellow
        $needRebuild = $true
    }
    if (-not (Test-Path (Join-Path $VENV_DIR "Scripts\python.exe"))) {
        Write-Host "  [!] Missing python.exe - venv corrupted" -ForegroundColor Yellow
        $needRebuild = $true
    }
    if (-not (Test-Path (Join-Path $VENV_DIR "Scripts\pip.exe"))) {
        Write-Host "  [!] Missing pip.exe - venv corrupted" -ForegroundColor Yellow
        $needRebuild = $true
    }
}

# If venv exists but is corrupted, remove it
if ($needRebuild) {
    Write-Host "  Removing corrupted virtual environment..." -ForegroundColor Yellow
    try {
        Remove-Item -Recurse -Force $VENV_DIR -ErrorAction Stop
    } catch {
        Write-Host ""
        Write-Host "  ========================================================" -ForegroundColor Red
        Write-Host "  [!] LOCKED FILES DETECTED" -ForegroundColor Red
        Write-Host "  ========================================================" -ForegroundColor Red
        Write-Host "  The .venv folder has files locked by another process." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Choose an option:" -ForegroundColor White
        Write-Host "    [1] Reboot and auto-resume installation" -ForegroundColor Gray
        Write-Host "    [2] Use alternate venv folder (.venv_new)" -ForegroundColor Gray
        Write-Host "    [3] Exit and fix manually" -ForegroundColor Gray
        Write-Host ""
        $choice = Read-Host "   Enter choice (1/2/3)"
        
        switch ($choice) {
            "1" {
                Write-Host ""
                Write-Host "  Setting up auto-resume after reboot..." -ForegroundColor Cyan
                "resume" | Out-File $resumeFile -Force
                # Create a scheduled task to run installer at next logon
                $installerPath = Join-Path $INSTALL_DIR "install_wreckhunter.ps1"
                $taskAction = "powershell.exe -ExecutionPolicy Bypass -File `"$installerPath`""
                schtasks /create /tn "WreckHunterInstallResume" /tr $taskAction /sc onlogon /f 2>&1 | Out-Null
                Write-Host "  [OK] Installer will resume automatically after reboot." -ForegroundColor Green
                Write-Host ""
                Write-Host "  Rebooting in 10 seconds... (Ctrl+C to cancel)" -ForegroundColor Yellow
                Start-Sleep -Seconds 10
                Restart-Computer -Force
                exit 0
            }
            "2" {
                Write-Host ""
                Write-Host "  Using alternate venv folder..." -ForegroundColor Cyan
                $VENV_DIR = Join-Path $INSTALL_DIR ".venv_new"
                $PYTHON_EXE = Join-Path $VENV_DIR "Scripts\python.exe"
                $PYTHONW_EXE = Join-Path $VENV_DIR "Scripts\pythonw.exe"
                $PIP_EXE = Join-Path $VENV_DIR "Scripts\pip.exe"
                # Remove old alternate if exists
                if (Test-Path $VENV_DIR) {
                    Remove-Item -Recurse -Force $VENV_DIR -ErrorAction SilentlyContinue
                }
            }
            default {
                Write-Host ""
                Write-Host "  Please close all terminals, VS Code, and any Python processes." -ForegroundColor Yellow
                Write-Host "  Then run this installer again." -ForegroundColor Yellow
                exit 1
            }
        }
    }
}

# Create venv if it doesn't exist
if (-not (Test-Path (Join-Path $VENV_DIR "Scripts\python.exe"))) {
    Write-Host "  Creating new virtual environment..." -ForegroundColor Gray
    python -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to create virtual environment" -ForegroundColor Red
        Write-Host "  Try running:  python -m pip install virtualenv" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "  [OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  [OK] Virtual environment exists and is valid" -ForegroundColor Green
}

# Final verification - test that python actually runs
$testResult = & $PYTHON_EXE -c "print('ok')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [!] Virtual environment python not working - rebuilding..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VENV_DIR -ErrorAction SilentlyContinue
    python -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Virtual environment rebuilt" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# STEP 3: Install Dependencies
# ============================================================================
Write-Host "[STEP 3/5] Installing dependencies (this may take 2-5 minutes)..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Upgrading pip..." -ForegroundColor Gray
& $PYTHON_EXE -m pip install --upgrade pip setuptools wheel --quiet 2>&1 | Out-Null

Write-Host "  Installing core packages..." -ForegroundColor Gray
$deps = @("h5py", "pyproj", "scipy", "numpy", "scikit-learn", "matplotlib")
foreach ($dep in $deps) {
    Write-Host "    - $dep" -ForegroundColor DarkGray
}
& $PIP_EXE install h5py pyproj scipy numpy scikit-learn matplotlib --quiet 2>&1 | Out-Null

Write-Host "  Installing optional packages..." -ForegroundColor Gray
& $PIP_EXE install PyMuPDF rasterio joblib pandas requests --quiet 2>&1 | Out-Null

Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# STEP 4: Create Desktop Shortcut
# ============================================================================
Write-Host "[STEP 4/5] Creating Desktop shortcut..." -ForegroundColor Yellow
Write-Host ""

if (-not $NoShortcuts) {
    $Desktop = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop")
    
    if (Test-Path $Desktop) {
        try {
            $ShortcutPath = Join-Path $Desktop "$APP_NAME.lnk"
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
            $Shortcut.TargetPath = $PYTHONW_EXE
            $Shortcut.Arguments = "`"$(Join-Path $InstallDir 'wreckhunter.py')`""
            $Shortcut.WorkingDirectory = $InstallDir
            $Shortcut.Description = "Great Lakes Shipwreck Detection Suite"
            $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,13"
            $Shortcut.Save()
            Write-Host "  [OK] Desktop shortcut created: `"$APP_NAME`"" -ForegroundColor Green
        } catch {
            Write-Host "  [WARNING] Could not create desktop shortcut" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  [SKIP] Shortcut creation disabled" -ForegroundColor Gray
}
Write-Host ""

# ============================================================================
# STEP 5: Create Start Menu Entry
# ============================================================================
Write-Host "[STEP 5/5] Creating Start Menu entry..." -ForegroundColor Yellow
Write-Host ""

if (-not $NoShortcuts) {
    $StartMenu = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs")
    $StartMenuDir = Join-Path $StartMenu $APP_NAME
    
    if (-not (Test-Path $StartMenuDir)) {
        New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
    }
    
    try {
        $WshShell = New-Object -ComObject WScript.Shell
        
        # Main app shortcut
        $Shortcut = $WshShell.CreateShortcut((Join-Path $StartMenuDir "$APP_NAME.lnk"))
        $Shortcut.TargetPath = $PYTHONW_EXE
        $Shortcut.Arguments = "`"$(Join-Path $InstallDir 'wreckhunter.py')`""
        $Shortcut.WorkingDirectory = $InstallDir
        $Shortcut.Description = "Great Lakes Shipwreck Detection Suite"
        $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,13"
        $Shortcut.Save()
        
        # CLI shortcut
        $Shortcut = $WshShell.CreateShortcut((Join-Path $StartMenuDir "$APP_NAME CLI.lnk"))
        $Shortcut.TargetPath = "cmd.exe"
        $Shortcut.Arguments = "/k cd /d `"$InstallDir`" & `"$PYTHON_EXE`" wreckhunter_cli.py --help"
        $Shortcut.WorkingDirectory = $InstallDir
        $Shortcut.Description = "Wreck Hunter 2000 Command Line"
        $Shortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
        $Shortcut.Save()
        
        # Uninstall shortcut
        $Shortcut = $WshShell.CreateShortcut((Join-Path $StartMenuDir "Uninstall.lnk"))
        $Shortcut.TargetPath = Join-Path $InstallDir "uninstall_wreckhunter.bat"
        $Shortcut.WorkingDirectory = $InstallDir
        $Shortcut.Description = "Remove Wreck Hunter 2000 shortcuts"
        $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,31"
        $Shortcut.Save()
        
        Write-Host "  [OK] Start Menu folder created: $APP_NAME" -ForegroundColor Green
        Write-Host "      - $APP_NAME (main app)" -ForegroundColor Gray
        Write-Host "      - $APP_NAME CLI (command line)" -ForegroundColor Gray
        Write-Host "      - Uninstall" -ForegroundColor Gray
    } catch {
        Write-Host "  [WARNING] Could not create Start Menu entry" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [SKIP] Start Menu creation disabled" -ForegroundColor Gray
}
Write-Host ""

# ============================================================================
# COMPLETE
# ============================================================================
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║                                                                       ║" -ForegroundColor Green
Write-Host "  ║   INSTALLATION COMPLETE!                                              ║" -ForegroundColor Green
Write-Host "  ║                                                                       ║" -ForegroundColor Green
Write-Host "  ╚═══════════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  You can now run Wreck Hunter 2000 by:" -ForegroundColor White
Write-Host ""
Write-Host "    [1] Double-click the Desktop icon: `"$APP_NAME`"" -ForegroundColor Gray
Write-Host "    [2] Open Start Menu -> `"$APP_NAME`"" -ForegroundColor Gray
Write-Host "    [3] Run from command line: python wreckhunter.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  To uninstall:" -ForegroundColor White
Write-Host "    Run uninstall_wreckhunter.bat or use Start Menu -> Uninstall" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""

if (-not $Silent) {
    $launch = Read-Host "Would you like to launch $APP_NAME now? (Y/N)"
    if ($launch -eq "Y" -or $launch -eq "y") {
        Write-Host ""
        Write-Host "  Launching $APP_NAME..." -ForegroundColor Cyan
        Start-Process $PYTHONW_EXE -ArgumentList "`"$(Join-Path $InstallDir 'wreckhunter.py')`""
    }
    Write-Host ""
    Read-Host "Press Enter to close this window"
}
