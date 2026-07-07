# Old Bass River Daily Report

This project creates a branded daily fishing report for **OldBassRiver.com**.

## What is included

### 1. Better website-ready HTML styling
The generated HTML now leans into the current Old Bass River look:
- IBM Plex styling
- clean black / off-white palette
- strong editorial headline treatment
- card-based hot-spot layout
- embedded live weather map

### 2. Simple editor UI instead of hand-editing JSON
A local Streamlit app lets you update:
- opening note
- hot spots
- what is working
- species to watch
- boating notes
- other local notes

It also gives you:
- live preview
- markdown download
- HTML download
- saved editorial JSON visibility

### 3. Morning automation helper
A scheduler helper is included so the report can be generated every morning through OpenClaw cron.

## Main files

- `app.py` — local editor UI
- `report_engine.py` — report logic, data fetching, rendering
- `generate_daily_report.py` — command-line generator
- `editorial_inputs.json` — your editable daily local-intel data
- `schedule_daily_report.cmd` — morning automation helper
- `run_dashboard.cmd` — launches the local editor UI
- `run_report.cmd` — generates the report once

## Generated outputs

Each run creates:
- `output/daily_report.md`
- `output/daily_report.html`

## Run the editor UI

```cmd
cd C:\Users\benfi\.openclaw\workspace\oldbassriver-report
run_dashboard.cmd
```

## Generate the report once

```cmd
cd C:\Users\benfi\.openclaw\workspace\oldbassriver-report
run_report.cmd
```

## Schedule the daily report

Default schedule:
- every day at **5:15 AM America/New_York**
- sends the generated markdown report to Telegram
- leaves the generated HTML ready for any separate publishing agent or workflow

```cmd
cd C:\Users\benfi\.openclaw\workspace\oldbassriver-report
schedule_daily_report.cmd
```

## Website workflow

Best daily workflow:
1. Open the editor UI
2. Update the real local bite intel
3. Generate the report
4. Hand off the generated HTML to your separate publishing workflow if needed

## Important note

The best version of this report is a **hybrid**:
- automated for conditions, tides, and public news
- editorial for hot spots, bait, pattern changes, and local signal

That keeps it useful without pretending public data alone can know where the bite is hottest.
