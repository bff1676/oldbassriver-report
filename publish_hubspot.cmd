@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [oldbassriver-report] Python was not found on PATH.
  exit /b 1
)

python generate_daily_report.py --publish-hubspot
