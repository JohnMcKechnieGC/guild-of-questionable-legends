from dataclasses import replace
from datetime import datetime
import sqlite3

import streamlit as st

from guild.interface import current_deck, database_path, portrait, _cached_deck
from guild.rules import STATS
from guild.storage import backup_bytes, normalize_portrait, update_card

st.caption("THE QUARTERMASTER'S DESK")
st.title("Deck Editor")
st.markdown("Browse all 36 guild members. Save a new name, biography, talent spread, or portrait. New deals use your saved deck; an ongoing match keeps its original cards.")

deck = current_deck()

if st.session_state.pop("deck_saved", False):
    st.success("Card saved. The next match will use your changes.")

names = {c.id: c.name for c in deck}
selected = st.selectbox("Character", list(names), format_func=lambda cid: names[cid], key="edit_card")
card = next(c for c in deck if c.id == selected)

left, right = st.columns([1, 1.6], gap="large")
with left:
    portrait(card, width=360)
    st.caption(f"Stable ID: {card.id} · 36 / 36 cards")
with right:
    with st.form(f"edit_{card.id}"):
        name = st.text_input("Name", value=card.name, max_chars=80, key=f"name_{card.id}")
        bio = st.text_area("Biography", value=card.bio, max_chars=600, key=f"bio_{card.id}")
        stats = []
        for start in (0, 2, 4):
            cols = st.columns(2)
            for i in range(start, start + 2):
                with cols[i - start]:
                    stats.append(st.number_input(STATS[i], min_value=1, max_value=100, value=card.stats[i], step=1, key=f"edit_{card.id}_{i}"))
        upload = st.file_uploader("Replace portrait", type=["png", "jpg", "jpeg", "webp"], max_upload_size=8, key=f"portrait_{card.id}", help="Up to 8 MB, at least 96×96 pixels. Center-cropped to 3:4 and stored inside SQLite.")
        if st.form_submit_button("Save card", type="primary", width="stretch"):
            try:
                image = normalize_portrait(upload.getvalue()) if upload else card.portrait
                update_card(replace(card, name=name, bio=bio, stats=tuple(stats), portrait=image), database_path())
                _cached_deck.clear()
                st.session_state.deck_saved = True
                st.rerun()
            except (ValueError, OSError, sqlite3.Error) as exc:
                st.error(str(exc))

st.divider()

st.subheader("Keep a copy of your guild")
st.markdown("Download a complete SQLite backup, including every portrait and saved edit. To restore one, stop the app and replace `data/deck.sqlite3` with the backup.")
st.download_button("Download deck backup", data=lambda: backup_bytes(database_path()),
                   file_name=f"guild-deck-{datetime.now():%Y%m%d-%H%M%S}.sqlite3",
                   mime="application/vnd.sqlite3", key="backup", icon=":material/download:")
