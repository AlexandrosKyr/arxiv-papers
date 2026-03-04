import streamlit as st
import json
import os
import subprocess
import sys

RESULTS_FILE = "results.json"

st.set_page_config(page_title="arXiv Weekly Digest", layout="wide")
st.title("arXiv Weekly Digest")

def load_results():
    if not os.path.exists(RESULTS_FILE):
        return None
    with open(RESULTS_FILE) as f:
        return json.load(f)

col1, col2 = st.columns([5, 1])

with col2:
    if st.button("Run Now", type="primary", use_container_width=True):
        with st.spinner("Fetching and filtering papers..."):
            result = subprocess.run(
                [sys.executable, "main.py"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
        if result.returncode == 0:
            st.rerun()
        else:
            st.error(result.stderr or "Pipeline failed.")

data = load_results()

if not data:
    st.info("No results yet. Click **Run Now** to fetch this week's papers.")
else:
    with col1:
        last_run = data["last_run"][:19].replace("T", " ")
        st.caption(f"Last updated: {last_run} · {len(data['papers'])} papers selected")

    for paper in data["papers"]:
        with st.expander(paper["title"]):
            st.markdown(f"**Why relevant:** _{paper['reason']}_")
            st.divider()
            authors = ", ".join(paper["authors"][:5])
            if len(paper["authors"]) > 5:
                authors += " et al."
            st.markdown(f"**Authors:** {authors}")
            st.markdown(f"**Categories:** {' · '.join(paper['categories'])}")
            if paper.get("venue"):
                st.markdown(f"**Venue:** {paper['venue']}")
            st.markdown(paper["summary"])
            st.markdown(f"[Open PDF]({paper['pdf_url']})")
