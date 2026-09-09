@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Run run.bat first to install dependencies.
  pause
  exit /b 1
)
"venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost
if errorlevel 1 (
  pause
  exit /b 1
)
