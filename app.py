"""Streamlit entry point. Launch with: streamlit run app.py"""
import streamlit as st

st.set_page_config(
    page_title="Guild of Questionable Legends",
    page_icon=":material/playing_cards:",
    layout="wide"
)

st.session_state.setdefault("match", None)
st.session_state.setdefault("match_serial", 0)
st.session_state.setdefault("ui_error", None)

page = st.navigation([
    st.Page("app_pages/play.py", title="Play", icon=":material/playing_cards:", default=True),
    st.Page("app_pages/editor.py", title="Deck Editor", icon=":material/auto_fix_high:"),
    st.Page("app_pages/rules.py", title="Rules", icon=":material/menu_book:"),
])

with st.sidebar:
    st.caption("THE GUILD CHARTER")
    st.markdown("36 misfits. Six talents.\n\nAn unreasonable amount of glory.")

page.run()
