@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [oldbassriver-report] Python was not found on PATH.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [oldbassriver-report] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 exit /b 1
  .venv\Scripts\python -m pip install --upgrade pip
  if errorlevel 1 exit /b 1
  .venv\Scripts\python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)

.venv\Scripts\python -m streamlit run app.py
