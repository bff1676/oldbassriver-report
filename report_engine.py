from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

import requests

ROOT = Path(__file__).parent
INPUT_PATH = ROOT / "editorial_inputs.json"
EXAMPLE_INPUT_PATH = ROOT / "editorial_inputs.example.json"
OUTPUT_DIR = ROOT / "output"
BASS_RIVER_LAT = 41.665
BASS_RIVER_LON = -70.1833
NOAA_TIDE_STATION = "8447504"
TIMEZONE = "America/New_York"
HEADERS = {"User-Agent": "OldBassRiverDailyReport/1.0"}
NEWS_QUERY = 'Cape Cod fishing OR striped bass Cape Cod OR bluefish Cape Cod OR tuna Cape Cod OR fluke Cape Cod when:7d'
NEWS_KEYWORDS = (
    "fishing",
    "fish",
    "striper",
    "striped bass",
    "bluefish",
    "tuna",
    "fluke",
    "flounder",
    "surf",
    "angler",
    "offshore",
    "charter",
)
WEATHER_MAP_URL = (
    "https://embed.windy.com/embed2.html?lat=41.665&lon=-70.1833&detailLat=41.665&detailLon=-70.1833"
    "&width=900&height=520&zoom=9&level=surface&overlay=radar&product=ecmwf&menu=&message=true"
    "&marker=true&calendar=now&pressure=&type=map&location=coordinates&detail=true&metricWind=mph"
    "&metricTemp=%C2%B0F&radarRange=-1"
)
WEATHER_MAP_PAGE_URL = "https://www.windy.com/41.665/-70.1833?radar,41.665,-70.1833,9"


@dataclass
class MarineSnapshot:
    wave_height_m: float | None
    wave_period_s: float | None
    wave_direction_deg: float | None
    water_temp_c: float | None
    air_temp_c: float | None
    wind_speed_kmh: float | None
    wind_gusts_kmh: float | None
    wind_direction_deg: float | None
    sunrise: str | None
    sunset: str | None


def default_editorial() -> dict[str, Any]:
    source = EXAMPLE_INPUT_PATH if EXAMPLE_INPUT_PATH.exists() else INPUT_PATH
    return json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}


def load_editorial() -> dict[str, Any]:
    source = INPUT_PATH if INPUT_PATH.exists() else EXAMPLE_INPUT_PATH
    return json.loads(source.read_text(encoding="utf-8")) if source.exists() else {}


def save_editorial(payload: dict[str, Any]) -> None:
    INPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fetch_json(url: str) -> dict[str, Any]:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_text(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def fetch_conditions() -> MarineSnapshot:
    marine_url = (
        "https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}"
        "&current=wave_height,wind_wave_height,swell_wave_height,wave_direction,wave_period,sea_surface_temperature"
        "&timezone=America%2FNew_York"
    ).format(lat=BASS_RIVER_LAT, lon=BASS_RIVER_LON)
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
        "&daily=sunrise,sunset&timezone=America%2FNew_York"
    ).format(lat=BASS_RIVER_LAT, lon=BASS_RIVER_LON)

    marine = fetch_json(marine_url)
    weather = fetch_json(weather_url)

    current_marine = marine.get("current", {})
    current_weather = weather.get("current", {})
    daily = weather.get("daily", {})

    return MarineSnapshot(
        wave_height_m=current_marine.get("wave_height"),
        wave_period_s=current_marine.get("wave_period"),
        wave_direction_deg=current_marine.get("wave_direction"),
        water_temp_c=current_marine.get("sea_surface_temperature"),
        air_temp_c=current_weather.get("temperature_2m"),
        wind_speed_kmh=current_weather.get("wind_speed_10m"),
        wind_gusts_kmh=current_weather.get("wind_gusts_10m"),
        wind_direction_deg=current_weather.get("wind_direction_10m"),
        sunrise=(daily.get("sunrise") or [None])[0],
        sunset=(daily.get("sunset") or [None])[0],
    )


def fetch_tides() -> list[dict[str, str]]:
    today = datetime.now().strftime("%Y%m%d")
    url = (
        "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions"
        f"&application=oldbassriver&begin_date={today}&end_date={today}"
        f"&datum=MLLW&station={NOAA_TIDE_STATION}&time_zone=lst_ldt&units=english&interval=hilo&format=json"
    )
    data = fetch_json(url)
    return data.get("predictions", [])


def fetch_news(limit: int = 4) -> list[dict[str, str]]:
    url = f"https://news.google.com/rss/search?q={quote_plus(NEWS_QUERY)}&hl=en-US&gl=US&ceid=US:en"
    xml_text = fetch_text(url)
    root = ET.fromstring(xml_text)

    items: list[dict[str, str]] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        if not title or not any(keyword in title.lower() for keyword in NEWS_KEYWORDS):
            continue
        link = (item.findtext("link") or "").strip()
        source_node = item.find("source")
        source = (source_node.text or "").strip() if source_node is not None else ""
        pub_date = (item.findtext("pubDate") or "").strip()
        items.append(
            {
                "title": title,
                "url": link,
                "source": source,
                "published": format_pub_date(pub_date),
            }
        )
        if len(items) >= limit:
            break
    return items


def build_report_bundle(editorial: dict[str, Any] | None = None) -> dict[str, Any]:
    editorial = editorial or load_editorial()
    snapshot = fetch_conditions()
    tides = fetch_tides()
    news = fetch_news(limit=4)
    markdown = build_markdown(editorial, snapshot, tides, news)
    html_report = build_html(editorial, snapshot, tides, news)
    return {
        "editorial": editorial,
        "snapshot": snapshot,
        "tides": tides,
        "news": news,
        "markdown": markdown,
        "html": html_report,
        "generated_at": datetime.now(),
    }


def write_outputs(bundle: dict[str, Any]) -> dict[str, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    markdown_path = OUTPUT_DIR / "daily_report.md"
    html_path = OUTPUT_DIR / "daily_report.html"
    markdown_path.write_text(bundle["markdown"], encoding="utf-8")
    html_path.write_text(bundle["html"], encoding="utf-8")
    return {"markdown": markdown_path, "html": html_path}


def format_pub_date(value: str) -> str:
    if not value:
        return ""
    try:
        dt = parsedate_to_datetime(value)
        return dt.strftime("%b %d")
    except Exception:
        return value


def feet_from_meters(value: float | None) -> float | None:
    return None if value is None else value * 3.28084


def fahrenheit_from_celsius(value: float | None) -> float | None:
    return None if value is None else (value * 9 / 5) + 32


def mph_from_kmh(value: float | None) -> float | None:
    return None if value is None else value * 0.621371


def cardinal(degrees: float | None) -> str:
    if degrees is None:
        return "n/a"
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(degrees / 45) % 8]


def rating_badge(value: str) -> str:
    lower = value.lower()
    if "hot" in lower:
        return "🔥"
    if "good" in lower:
        return "✅"
    if "watch" in lower:
        return "👀"
    return "⚠️"


def boating_options(snapshot: MarineSnapshot) -> list[dict[str, str]]:
    wave_ft = feet_from_meters(snapshot.wave_height_m) or 0.0
    wind_mph = mph_from_kmh(snapshot.wind_speed_kmh) or 0.0

    if wave_ft <= 1.5 and wind_mph <= 12:
        overall = "Excellent"
        detail = "Protected water, skiffs, kayaks, and nearshore runs all look reasonable."
    elif wave_ft <= 2.5 and wind_mph <= 18:
        overall = "Good early"
        detail = "Small boats should favor the morning window before afternoon breeze adds chop."
    elif wave_ft <= 4.0 and wind_mph <= 25:
        overall = "Selective"
        detail = "Okay for experienced crews in the right boat, but protected water and shore options are cleaner."
    else:
        overall = "Caution"
        detail = "This is more of a shore, jetty, or protected-water day than an open-water comfort day."

    return [
        {"mode": "Shore / Jetty", "status": "Best bet", "notes": "Most reliable option regardless of afternoon chop."},
        {"mode": "Kayak / SUP", "status": "Good" if wave_ft <= 1.5 and wind_mph <= 12 else "Use judgment", "notes": "Stay inside the river and protected water if wind builds."},
        {"mode": "Small skiff / bay boat", "status": overall, "notes": detail},
        {"mode": "Open Sound run", "status": "Early window" if wave_ft <= 3.0 else "Only if conditions settle", "notes": "Check the latest marine forecast before committing outside the river mouth."},
    ]


def build_markdown(editorial: dict[str, Any], snapshot: MarineSnapshot, tides: list[dict[str, str]], news: list[dict[str, str]]) -> str:
    now = datetime.now().strftime("%B %d, %Y, %I:%M %p ET")
    wave_ft = feet_from_meters(snapshot.wave_height_m)
    water_f = fahrenheit_from_celsius(snapshot.water_temp_c)
    air_f = fahrenheit_from_celsius(snapshot.air_temp_c)
    wind_mph = mph_from_kmh(snapshot.wind_speed_kmh)
    gust_mph = mph_from_kmh(snapshot.wind_gusts_kmh)

    lines = [
        f"# {editorial.get('report_name', 'Old Bass River Daily Fishing Report')}",
        f"Updated {now}",
        "",
        f"**{editorial.get('location', 'Cape Cod')}**",
        "",
        editorial.get("opening_note", ""),
        "",
        "## Today’s quick read",
        f"- Air temp: {fmt_num(air_f, '°F')}",
        f"- Water temp: {fmt_num(water_f, '°F')}",
        f"- Wind: {fmt_num(wind_mph, 'mph')} from {cardinal(snapshot.wind_direction_deg)} (gusts {fmt_num(gust_mph, 'mph')})",
        f"- Wave height: {fmt_num(wave_ft, 'ft')} at {fmt_num(snapshot.wave_period_s, 's')} from {cardinal(snapshot.wave_direction_deg)}",
        f"- Sunrise / Sunset: {format_clock(snapshot.sunrise)} / {format_clock(snapshot.sunset)}",
        "",
        "## Live weather map",
        f"- Interactive radar and weather map: {WEATHER_MAP_PAGE_URL}",
        "",
        "## Hottest spots right now",
    ]

    for spot in editorial.get("hot_spots", []):
        species = ", ".join(spot.get("species", []))
        lines.extend(
            [
                f"- {rating_badge(spot.get('rating', 'Watch'))} **{spot.get('zone', 'Spot')}** ({spot.get('rating', 'Watch')})",
                f"  - Species: {species}",
                f"  - Best window: {spot.get('best_window', 'Check tide and light')}",
                f"  - Access: {spot.get('access', 'Varies')}",
                f"  - Notes: {spot.get('notes', '')}",
            ]
        )

    lines.extend(["", "## Boating options"])
    for option in boating_options(snapshot):
        lines.append(f"- **{option['mode']}**: {option['status']} — {option['notes']}")

    if editorial.get("boating_notes"):
        lines.append("")
        lines.append("### Local boating notes")
        for note in editorial.get("boating_notes", []):
            lines.append(f"- {note}")

    lines.extend(["", "## Tide table, Bass River (South Yarmouth)"])
    for tide in tides:
        tide_type = "High" if tide.get("type") == "H" else "Low"
        lines.append(f"- {tide_type}: {format_clock(tide.get('t'))} ({tide.get('v')} ft)")

    lines.extend(["", "## What’s working"])
    for item in editorial.get("what_is_working", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Species to watch"])
    for item in editorial.get("species_watch", []):
        lines.append(f"- {item}")

    if editorial.get("other_interest"):
        lines.extend(["", "## Other things worth watching"])
        for item in editorial.get("other_interest", []):
            lines.append(f"- {item}")

    lines.extend(["", "## Fishing news"])
    for item in news:
        source = f"{item['source']}: " if item.get("source") else ""
        published = f" ({item['published']})" if item.get("published") else ""
        lines.append(f"- {source}{item['title']}{published}")

    lines.extend(
        [
            "",
            "---",
            "This report blends public conditions data with local editorial judgment. For the hottest-spot section, same-day local intel matters more than any feed.",
        ]
    )

    return "\n".join(lines)


def build_html(editorial: dict[str, Any], snapshot: MarineSnapshot, tides: list[dict[str, str]], news: list[dict[str, str]]) -> str:
    hot_spots_html = "".join(
        f"<div class='obr-card'><div class='obr-card-title'>{rating_badge(spot.get('rating', 'Watch'))} {html.escape(spot.get('zone', 'Spot'))}</div>"
        f"<div class='obr-card-meta'>{html.escape(spot.get('rating', 'Watch'))} • {html.escape(', '.join(spot.get('species', [])))}</div>"
        f"<p><strong>Best window:</strong> {html.escape(spot.get('best_window', 'Check tide and light'))}</p>"
        f"<p><strong>Access:</strong> {html.escape(spot.get('access', 'Varies'))}</p>"
        f"<p>{html.escape(spot.get('notes', ''))}</p></div>"
        for spot in editorial.get("hot_spots", [])
    )
    boating_html = "".join(
        f"<li><strong>{html.escape(item['mode'])}:</strong> {html.escape(item['status'])} — {html.escape(item['notes'])}</li>"
        for item in boating_options(snapshot)
    )
    tides_html = "".join(
        f"<li><strong>{'High' if tide.get('type') == 'H' else 'Low'}:</strong> {html.escape(format_clock(tide.get('t')))} ({html.escape(tide.get('v', ''))} ft)</li>"
        for tide in tides
    )
    news_html = "".join(
        f"<li><strong>{html.escape(item.get('source', 'News'))}:</strong> <a href='{html.escape(item.get('url', ''))}' target='_blank' rel='noopener'>{html.escape(item.get('title', ''))}</a></li>"
        for item in news
    )
    quick_list = [
        f"Air temp: {html.escape(fmt_num(fahrenheit_from_celsius(snapshot.air_temp_c), '°F'))}",
        f"Water temp: {html.escape(fmt_num(fahrenheit_from_celsius(snapshot.water_temp_c), '°F'))}",
        f"Wind: {html.escape(fmt_num(mph_from_kmh(snapshot.wind_speed_kmh), 'mph'))} from {html.escape(cardinal(snapshot.wind_direction_deg))}",
        f"Wave height: {html.escape(fmt_num(feet_from_meters(snapshot.wave_height_m), 'ft'))} at {html.escape(fmt_num(snapshot.wave_period_s, 's'))}",
        f"Sunrise / Sunset: {html.escape(format_clock(snapshot.sunrise))} / {html.escape(format_clock(snapshot.sunset))}",
    ]
    quick_html = "".join(f"<li>{item}</li>" for item in quick_list)
    working_html = "".join(f"<li>{html.escape(item)}</li>" for item in editorial.get("what_is_working", []))
    species_html = "".join(f"<li>{html.escape(item)}</li>" for item in editorial.get("species_watch", []))
    other_html = "".join(f"<li>{html.escape(item)}</li>" for item in editorial.get("other_interest", []))
    boating_notes_html = "".join(f"<li>{html.escape(item)}</li>" for item in editorial.get("boating_notes", []))
    now = datetime.now().strftime("%B %d, %Y, %I:%M %p ET")

    return f"""<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{html.escape(editorial.get('report_name', 'Old Bass River Daily Fishing Report'))}</title>
<link rel='preconnect' href='https://fonts.googleapis.com'>
<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap' rel='stylesheet'>
<style>
:root {{ --ink:#0f0f10; --muted:#6d6d73; --line:#d7d7d9; --bg:#f7f6f2; --card:#ffffff; }}
body {{ font-family:'IBM Plex Sans', Arial, sans-serif; color:var(--ink); background:var(--bg); line-height:1.55; margin:0; }}
a {{ color:var(--ink); }}
.obr-wrap {{ max-width: 1080px; margin: 0 auto; padding: 28px 20px 48px; }}
.obr-kicker {{ letter-spacing:.08em; text-transform:uppercase; font-size:12px; color:var(--muted); font-family:'IBM Plex Mono', monospace; }}
.obr-title {{ font-size:40px; line-height:1.05; margin:10px 0 8px; }}
.obr-subtitle {{ max-width:760px; color:#232327; font-size:17px; }}
.obr-rule {{ border-top:2px solid var(--ink); margin:26px 0 18px; }}
.obr-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:16px; }}
.obr-card {{ border:1px solid var(--line); border-radius:16px; padding:18px; background:var(--card); }}
.obr-card-title {{ font-size:18px; font-weight:700; margin-bottom:5px; }}
.obr-card-meta {{ font-family:'IBM Plex Mono', monospace; font-size:12px; color:var(--muted); margin-bottom:10px; }}
.obr-section {{ margin-top:30px; }}
.obr-list {{ padding-left:20px; }}
.obr-list li {{ margin-bottom:8px; }}
.obr-stat {{ border:1px solid var(--line); padding:14px; border-radius:14px; background:var(--card); }}
.obr-stat-label {{ font-family:'IBM Plex Mono', monospace; font-size:12px; text-transform:uppercase; color:var(--muted); }}
.obr-stat-value {{ margin-top:6px; font-size:24px; font-weight:700; }}
.obr-map-frame {{ width:100%; min-height:520px; border:1px solid var(--line); border-radius:16px; background:var(--card); }}
.obr-map-note {{ color:var(--muted); font-size:14px; margin-top:8px; }}
</style>
</head>
<body>
<div class='obr-wrap'>
  <div class='obr-kicker'>41°40′N 70°11′W · Bass River, Dennis & Yarmouth · Cape Cod</div>
  <h1 class='obr-title'>{html.escape(editorial.get('report_name', 'Old Bass River Daily Fishing Report'))}</h1>
  <p class='obr-subtitle'>{html.escape(editorial.get('opening_note', ''))}</p>
  <div class='obr-rule'></div>
  <p><strong>Updated:</strong> {html.escape(now)}</p>

  <div class='obr-grid'>
    <div class='obr-stat'><div class='obr-stat-label'>Air temp</div><div class='obr-stat-value'>{html.escape(fmt_num(fahrenheit_from_celsius(snapshot.air_temp_c), '°F'))}</div></div>
    <div class='obr-stat'><div class='obr-stat-label'>Water temp</div><div class='obr-stat-value'>{html.escape(fmt_num(fahrenheit_from_celsius(snapshot.water_temp_c), '°F'))}</div></div>
    <div class='obr-stat'><div class='obr-stat-label'>Wind</div><div class='obr-stat-value'>{html.escape(fmt_num(mph_from_kmh(snapshot.wind_speed_kmh), 'mph'))} {html.escape(cardinal(snapshot.wind_direction_deg))}</div></div>
    <div class='obr-stat'><div class='obr-stat-label'>Wave height</div><div class='obr-stat-value'>{html.escape(fmt_num(feet_from_meters(snapshot.wave_height_m), 'ft'))}</div></div>
  </div>

  <div class='obr-section'>
    <h2>Today’s quick read</h2>
    <ul class='obr-list'>{quick_html}</ul>
  </div>

  <div class='obr-section'>
    <h2>Live weather map</h2>
    <iframe class='obr-map-frame' src='{WEATHER_MAP_URL}' title='Bass River live weather map'></iframe>
    <p class='obr-map-note'>Interactive weather and radar view for Bass River and Nantucket Sound. <a href='{WEATHER_MAP_PAGE_URL}' target='_blank' rel='noopener'>Open full-screen map</a>.</p>
  </div>

  <div class='obr-section'>
    <h2>Hottest spots right now</h2>
    <div class='obr-grid'>{hot_spots_html}</div>
  </div>

  <div class='obr-section'>
    <h2>Boating options</h2>
    <ul class='obr-list'>{boating_html}</ul>
    <ul class='obr-list'>{boating_notes_html}</ul>
  </div>

  <div class='obr-section'>
    <h2>Tide table, Bass River (South Yarmouth)</h2>
    <ul class='obr-list'>{tides_html}</ul>
  </div>

  <div class='obr-section obr-grid'>
    <div class='obr-card'><h3>What’s working</h3><ul class='obr-list'>{working_html}</ul></div>
    <div class='obr-card'><h3>Species to watch</h3><ul class='obr-list'>{species_html}</ul></div>
    <div class='obr-card'><h3>Other things worth watching</h3><ul class='obr-list'>{other_html}</ul></div>
  </div>

  <div class='obr-section'>
    <h2>Fishing news</h2>
    <ul class='obr-list'>{news_html}</ul>
  </div>

  <div class='obr-section'>
    <p><em>This report blends public conditions data with local editorial judgment. For the hottest-spot section, same-day local intel matters more than any feed.</em></p>
  </div>
</div>
</body>
</html>
"""


def fmt_num(value: float | None, suffix: str) -> str:
    if value is None:
        return f"n/a {suffix}".strip()
    return f"{value:.1f}{suffix}"


def format_clock(value: str | None) -> str:
    if not value:
        return "n/a"
    try:
        if "T" in value:
            dt = datetime.fromisoformat(value)
        else:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return value
