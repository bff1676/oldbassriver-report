# Old Bass River Daily Report

This project creates a branded daily fishing report for **OldBassRiver.com**.

## What is included

### 1. Better website-ready HTML styling
The generated HTML now leans into the current Old Bass River look:
- IBM Plex styling
- clean black / off-white palette
- strong editorial headline treatment
- card-based hot-spot layout
- easy HubSpot-ready HTML output

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
- direct HubSpot publish button
- saved editorial JSON visibility

### 3. Morning automation helper
A scheduler helper is included so the report can be generated every morning through OpenClaw cron.

### 4. Direct HubSpot publishing
The project now supports direct **HubSpot blog-post publishing**.

That is handled through a local config file named `hubspot_publish.json` that is intentionally ignored by git.

## Main files

- `app.py` — local editor UI
- `report_engine.py` — report logic, data fetching, rendering
- `hubspot_publish.py` — HubSpot publishing logic
- `generate_daily_report.py` — command-line generator and optional publisher
- `editorial_inputs.json` — your editable daily local-intel data
- `hubspot_publish.example.json` — example HubSpot publishing config
- `schedule_daily_report.cmd` — morning automation helper
- `run_dashboard.cmd` — launches the local editor UI
- `run_report.cmd` — generates the report once
- `publish_hubspot.cmd` — generates the report and publishes it to HubSpot

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

## Publish directly to HubSpot

1. Copy the example config:

```cmd
cd C:\Users\benfi\.openclaw\workspace\oldbassriver-report
copy hubspot_publish.example.json hubspot_publish.json
```

2. Edit `hubspot_publish.json` and fill in:
- `access_token`
- `blog_post.content_group_id`
- `blog_post.author_id`
- optional `tag_ids`
- optional `post_id` if you want to update one fixed post instead of creating a new one

3. Publish:

```cmd
cd C:\Users\benfi\.openclaw\workspace\oldbassriver-report
publish_hubspot.cmd
```

Or:

```cmd
python generate_daily_report.py --publish-hubspot
```

## HubSpot target and current assumption

Right now the direct integration targets **HubSpot blog posts** because that is the cleanest fit for a daily fishing report archive.

If you want this to update one fixed **site page** instead of creating daily posts, that is still doable, but I would want the exact destination page/module setup before wiring that path.

## Schedule the daily report

Default schedule:
- every day at **5:15 AM America/New_York**
- sends the generated markdown report to Telegram
- if HubSpot config exists, it also attempts direct HubSpot publishing first

```cmd
cd C:\Users\benfi\.openclaw\workspace\oldbassriver-report
schedule_daily_report.cmd
```

## Website workflow

Best daily workflow:
1. Open the editor UI
2. Update the real local bite intel
3. Generate the report
4. Publish straight to HubSpot from the app or CLI

## Important note

The best version of this report is a **hybrid**:
- automated for conditions, tides, and public news
- editorial for hot spots, bait, pattern changes, and local signal

That keeps it useful without pretending public data alone can know where the bite is hottest.
