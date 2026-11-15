from pathlib import Path
import streamlit as st

st.caption("THE GUILD CHARTER")
st.title("Rules of questionable conduct")
st.markdown((Path(__file__).resolve().parents[1] / "RULES.md").read_text(encoding="utf-8"))
