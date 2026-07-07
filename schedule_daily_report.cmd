@echo off
setlocal
cd /d "%~dp0"

where openclaw.cmd >nul 2>nul
if errorlevel 1 (
  echo [oldbassriver-report] openclaw.cmd was not found on PATH.
  exit /b 1
)

set JOB_NAME=%~1
if "%JOB_NAME%"=="" set JOB_NAME=oldbassriver-daily-report

set CRON_EXPR=%~2
if "%CRON_EXPR%"=="" set CRON_EXPR=15 5 * * *

set DELIVERY_CHANNEL=%~3
if "%DELIVERY_CHANNEL%"=="" set DELIVERY_CHANNEL=telegram

set DELIVERY_TO=%~4
if "%DELIVERY_TO%"=="" set DELIVERY_TO=8763388762

set TZ=America/New_York
set GENERATOR=%~dp0generate_daily_report.py
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
set MESSAGE=In the oldbassriver-report workspace, run "%PYTHON_EXE%" "%GENERATOR%" and send the generated markdown daily fishing report to the user. Mention that the matching HTML file is ready in output\daily_report.html for the separate publishing workflow.

echo [oldbassriver-report] Creating OpenClaw cron job...
openclaw.cmd cron add --name "%JOB_NAME%" --cron "%CRON_EXPR%" --tz "%TZ%" --session isolated --announce --light-context --channel "%DELIVERY_CHANNEL%" --to "%DELIVERY_TO%" --message "%MESSAGE%" --tools exec,read --timeout-seconds 300
