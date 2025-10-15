@echo off
REM === BAGFILE ANALYSIS SYSTEM ENVIRONMENT & GUI LAUNCHER ===
REM 1. Create/activate conda environment
set ENV_NAME=Nautidog
set PY_VER=3.12.3

REM Check if conda is available
where conda >nul 2>nul
if errorlevel 1 (
    echo Conda not found. Please install Anaconda or Miniconda and add to PATH.
    exit /b 1
)

REM Create environment if it doesn't exist
conda info --envs | findstr /C:"%ENV_NAME%" >nul
if errorlevel 1 (
    echo Creating conda environment %ENV_NAME%...
    conda create -y -n %ENV_NAME% python=%PY_VER%
)

REM Activate environment
call conda activate %ENV_NAME%

REM Install required packages
conda install -y numpy scipy matplotlib rasterio pillow pyproj pandas jupyter flask
REM For Rust-PyO3 integration
pip install maturin

REM 2. Build Rust extension
cd /d %~dp0
cargo build --release
copy target\release\bag_processor.pyd development_and_tools

REM 3. Run the unified GUI
cd development_and_tools
python enhanced_bag_gui.py

REM 4. Generate visualizations and webpage (including PDF results)
python bag_visualization_generator.py

REM 5. Open the results webpage
start ..\development_and_tools\bagfiles\reconstruction_gallery.html

REM 6. All outputs are now available for sharing/viewing

REM 7. Commit all changes to git
cd /d %~dp0
REM Add all new/changed files
call git add .
REM Commit with timestamp
set dt=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%
call git commit -m "Automated: Full analysis, GUI, and visualization outputs [%dt%]"
REM Push to remote
call git push

echo === BAGFILE ANALYSIS SYSTEM COMPLETE ===
pause