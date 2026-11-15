"""Shared presentation helpers and guarded session callbacks."""
import os
from pathlib import Path
import sqlite3

import streamlit as st

from guild.rules import Card, Player, STATS, act, new_match
from guild.storage import DEFAULT_DB, load_deck


def database_path() -> Path:
    return Path(os.environ.get("GUILD_DB_PATH", str(DEFAULT_DB)))


@st.cache_data(max_entries=4, show_spinner=False)
def _cached_deck(path: str, modified: int, size: int) -> tuple[Card, ...]:
    return load_deck(Path(path))


def current_deck() -> tuple[Card, ...]:
    path = database_path()
    try:
        info = path.stat()
        return _cached_deck(str(path.resolve()), info.st_mtime_ns, info.st_size)
    except (OSError, ValueError, sqlite3.Error) as exc:
        st.error(f"The saved deck could not be loaded: {exc}")
        st.stop()


def start_match(players: tuple[Player, ...], serial: int, rematch: bool = False) -> None:
    if serial != st.session_state.match_serial:
        return
    if st.session_state.match is not None and not rematch:
        return
    try:
        st.session_state.match = new_match(current_deck(), players)
        st.session_state.match_serial += 1
        st.session_state.ui_error = None
    except ValueError as exc:
        st.session_state.ui_error = str(exc)


def transition(action: str, revision: int, serial: int, stat: int | None = None) -> None:
    if serial == st.session_state.match_serial and st.session_state.match is not None:
        st.session_state.match = act(st.session_state.match, action, revision, stat)


def leave_match(serial: int) -> None:
    if serial == st.session_state.match_serial:
        st.session_state.match = None
        st.session_state.match_serial += 1


def action_button(label: str, action: str, key: str, stat: int | None = None, primary=False) -> None:
    match = st.session_state.match
    st.button(label, key=key, width="stretch", type="primary" if primary else "secondary",
              on_click=transition, args=(action, match.revision, st.session_state.match_serial, stat))


def portrait(card: Card, width="stretch") -> None:
    st.image(card.portrait, alt=f"Illustrated portrait of {card.name}", width=width)


def stat_list(card: Card) -> None:
    for label, value in zip(STATS, card.stats):
        st.markdown(f"{label} **{value}**")
        st.progress(value / 100)
