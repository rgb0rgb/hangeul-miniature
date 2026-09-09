@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  python -m venv venv
  if errorlevel 1 goto :failed
)
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
"venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto :failed
exit /b 0
:failed
echo Startup failed. Check Python installation and the error above.
pause
exit /b 1
