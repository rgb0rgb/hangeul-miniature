@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo Python 3.10 or later was not found. Install Python from python.org or activate your Python environment.
  pause
  exit /b 1
)
if not exist "venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv venv
  if errorlevel 1 goto :failed
)
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
"venv\Scripts\python.exe" -m streamlit run app.py --server.address localhost
if errorlevel 1 goto :failed
exit /b 0
:failed
echo Startup failed. Check Python installation and the error above.
pause
exit /b 1
