@echo off
echo ========================================
echo  Cloud Render Node Installer
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

:: Create virtual environment
echo Creating virtual environment...
python -m venv render_node_env
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created
echo.

:: Install dependencies
echo Installing dependencies...
call render_node_env\Scripts\activate.bat
pip install requests uuid platform winreg
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

:: Create node configuration
echo Creating node configuration...
set /p NODE_NAME="Enter a name for this node (or press Enter for auto-generated): "

if "%NODE_NAME%"=="" (
    set CONFIG_JSON={\"node_name\": \"\", \"computer_name\": \"%COMPUTERNAME%\"}
) else (
    set CONFIG_JSON={\"node_name\": \"%NODE_NAME%\", \"computer_name\": \"%COMPUTERNAME%\"}
)

echo %CONFIG_JSON% > node_config.json

echo ✅ Node configuration created
echo.

:: Create run script
echo Creating run script...
echo @echo off > run_node.bat
echo call render_node_env\Scripts\activate.bat >> run_node.bat
echo python injector.py >> run_node.bat
echo pause >> run_node.bat

echo ✅ Run script created
echo.

:: Test the installation
echo Testing installation...
python -c "import requests; import json; print('✅ All imports successful')"
if errorlevel 1 (
    echo ❌ Installation test failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  INSTALLATION COMPLETE!
echo ========================================
echo.
echo 📝 What was installed:
echo    - Python virtual environment
echo    - Required packages
echo    - Node configuration
echo    - Run script (run_node.bat)
echo.
