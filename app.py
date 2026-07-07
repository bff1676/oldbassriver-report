from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from report_engine import build_report_bundle, default_editorial, load_editorial, save_editorial, write_outputs

ROOT = Path(__file__).parent

st.set_page_config(page_title="Old Bass River Daily Report Editor", layout="wide")

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1300px;}
      .obr-hero {padding: 1.2rem 0 1.1rem; border-bottom: 2px solid #111; margin-bottom: 1rem;}
      .obr-kicker {font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; color: #666;}
      .obr-title {font-size: 2.5rem; line-height: 1.0; font-weight: 700; margin: 0.35rem 0;}
      .obr-sub {max-width: 900px; color: #222;}
      .obr-note {padding: 0.9rem 1rem; border: 1px solid rgba(0,0,0,0.15); border-radius: 14px; background: #faf8f2;}
    </style>
    """,
    unsafe_allow_html=True,
)

if "editorial" not in st.session_state:
    st.session_state.editorial = load_editorial() or default_editorial()

st.markdown("<div class='obr-hero'><div class='obr-kicker'>41°40′N 70°11′W · Bass River · Cape Cod</div><div class='obr-title'>Old Bass River Daily Report Editor</div><div class='obr-sub'>Update the bite intel in a simple form and generate the daily website report with a live weather map in the preview.</div></div>", unsafe_allow_html=True)

left, right = st.columns([1.0, 1.2])

with left:
    with st.form("editorial_form"):
        editorial = st.session_state.editorial
        st.subheader("Report basics")
        report_name = st.text_input("Report name", value=editorial.get("report_name", "Old Bass River Daily Fishing Report"))
        location = st.text_input("Location line", value=editorial.get("location", "Bass River, Dennis & Yarmouth, Cape Cod"))
        opening_note = st.text_area("Opening note", value=editorial.get("opening_note", ""), height=140)

        st.subheader("Hot spots")
        hot_spots = editorial.get("hot_spots", [])
        updated_spots = []
        for idx in range(max(4, len(hot_spots))):
            spot = hot_spots[idx] if idx < len(hot_spots) else {}
            with st.expander(f"Spot {idx + 1}", expanded=idx < 2):
                zone = st.text_input(f"Zone {idx + 1}", value=spot.get("zone", ""), key=f"zone_{idx}")
                rating = st.selectbox(
                    f"Rating {idx + 1}",
                    options=["Hot", "Good", "Watch", "Needs local confirmation"],
                    index=["Hot", "Good", "Watch", "Needs local confirmation"].index(spot.get("rating", "Watch"))
                    if spot.get("rating", "Watch") in ["Hot", "Good", "Watch", "Needs local confirmation"]
                    else 2,
                    key=f"rating_{idx}",
                )
                species = st.text_input(f"Species {idx + 1} (comma separated)", value=", ".join(spot.get("species", [])), key=f"species_{idx}")
                best_window = st.text_input(f"Best window {idx + 1}", value=spot.get("best_window", ""), key=f"window_{idx}")
                access = st.text_input(f"Access {idx + 1}", value=spot.get("access", ""), key=f"access_{idx}")
                notes = st.text_area(f"Notes {idx + 1}", value=spot.get("notes", ""), height=90, key=f"notes_{idx}")
                if zone.strip():
                    updated_spots.append(
                        {
                            "zone": zone.strip(),
                            "rating": rating,
                            "species": [part.strip() for part in species.split(",") if part.strip()],
                            "best_window": best_window.strip(),
                            "access": access.strip(),
                            "notes": notes.strip(),
                        }
                    )

        st.subheader("Other editable sections")
        what_is_working = st.text_area("What’s working (one item per line)", value="\n".join(editorial.get("what_is_working", [])), height=100)
        species_watch = st.text_area("Species to watch (one per line)", value="\n".join(editorial.get("species_watch", [])), height=100)
        boating_notes = st.text_area("Boating notes (one per line)", value="\n".join(editorial.get("boating_notes", [])), height=100)
        other_interest = st.text_area("Other things worth watching (one per line)", value="\n".join(editorial.get("other_interest", [])), height=100)

        submitted = st.form_submit_button("Save editorial inputs", use_container_width=True)
        if submitted:
            new_editorial = {
                "report_name": report_name.strip(),
                "location": location.strip(),
                "opening_note": opening_note.strip(),
                "hot_spots": updated_spots,
                "what_is_working": [line.strip() for line in what_is_working.splitlines() if line.strip()],
                "species_watch": [line.strip() for line in species_watch.splitlines() if line.strip()],
                "boating_notes": [line.strip() for line in boating_notes.splitlines() if line.strip()],
                "other_interest": [line.strip() for line in other_interest.splitlines() if line.strip()],
            }
            save_editorial(new_editorial)
            st.session_state.editorial = new_editorial
            st.success("Editorial inputs saved.")

    st.markdown("<div class='obr-note'><strong>Tip:</strong> The automated parts are conditions, tides, news, and the live weather map. The section that matters most for readers is still your real same-day bite intel, hot spots, bait, and access notes.</div>", unsafe_allow_html=True)

with right:
    if st.button("Generate fresh report", use_container_width=True):
            bundle = build_report_bundle(st.session_state.editorial)
            paths = write_outputs(bundle)
            st.session_state.bundle = bundle
            st.session_state.paths = paths
            st.success(f"Generated {paths['markdown'].name} and {paths['html'].name}")

    if "bundle" not in st.session_state:
        st.session_state.bundle = build_report_bundle(st.session_state.editorial)
        st.session_state.paths = write_outputs(st.session_state.bundle)

    bundle = st.session_state.bundle
    paths = st.session_state.paths

    st.caption(f"Last generated: {bundle['generated_at'].strftime('%Y-%m-%d %I:%M %p ET')}")

    preview_tab, markdown_tab, html_tab, files_tab = st.tabs(["Live preview", "Markdown", "HTML", "Files"])

    with preview_tab:
        components.html(bundle["html"], height=1200, scrolling=True)

    with markdown_tab:
        st.download_button("Download markdown", data=bundle["markdown"], file_name="daily_report.md", mime="text/markdown", use_container_width=True)
        st.code(bundle["markdown"], language="markdown")

    with html_tab:
        st.download_button("Download HTML", data=bundle["html"], file_name="daily_report.html", mime="text/html", use_container_width=True)
        st.code(bundle["html"], language="html")

    with files_tab:
        st.write("Generated files")
        st.write(str(paths["markdown"]))
        st.write(str(paths["html"]))
        st.write("Current editorial JSON")
        st.code(json.dumps(st.session_state.editorial, indent=2), language="json")
