from dataclasses import replace
from pathlib import Path
import shutil

import pytest
from streamlit.testing.v1 import AppTest

from guild.rules import Player, new_match
from guild.storage import DEFAULT_DB, load_deck

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app(tmp_path, monkeypatch):
    path = tmp_path / "deck.sqlite3"
    shutil.copyfile(DEFAULT_DB, path)
    monkeypatch.setenv("GUILD_DB_PATH", str(path))
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run(), path


@pytest.mark.parametrize("count", [2, 3, 4])
def test_deal_rerun_private_reveal_and_comparison(app, count):
    at, path = app
    at.segmented_control(key="player_count").set_value(count).run()
    at.button(key="FormSubmitter:new_game-Shuffle & deal").click().run()
    assert not at.exception
    match = at.session_state.match
    assert len(match.players) == count
    assert [len(p) for p in match.piles] == [36 // count] * count
    at.run()
    assert at.session_state.match == match
    # Select a reproducible human-first deal to verify the privacy gate.
    for seed in range(50):
        candidate = new_match(load_deck(path), match.players, seed)
        if candidate.phase == "pass":
            break
    at.session_state.match = candidate
    at.run()
    assert len(at.image) == 0
    at.button(key="reveal").click().run()
    assert at.session_state.match.phase == "choose"
    assert len(at.image) == 1
    at.button(key="stat_0").click().run()
    assert not at.exception
    result = at.session_state.match
    assert result.phase == "result" and result.round_number == 1
    at.run()
    assert at.session_state.match == result
    at.button(key="continue").click().run()
    assert at.session_state.match.round_number == 1


def test_computer_does_not_advance_on_rerun(app):
    at, path = app
    players = (Player("A"), Player("Ledger", True))
    match = next(m for seed in range(50) if (m := new_match(load_deck(path), players, seed)).phase == "computer")
    at.session_state.match = match
    at.run()
    at.run()
    assert at.session_state.match == match
    at.button(key="computer").click().run()
    after = at.session_state.match
    assert after.round_number == 1
    at.run()
    assert at.session_state.match == after
    assert not at.exception


def test_editor_validation_save_and_match_snapshot(app):
    at, path = app
    at.session_state.match = new_match(load_deck(path), (Player("A"), Player("Ledger", True)), 2)
    original = at.session_state.match.deck[0]
    at.switch_page("app_pages/editor.py").run()
    assert not at.exception
    at.text_input(key="name_gql-01").set_value(" ")
    at.button(key="FormSubmitter:edit_gql-01-Save card").click().run()
    assert at.error and load_deck(path)[0] == original
    at.text_input(key="name_gql-01").set_value("Bixby the Revised")
    at.text_area(key="bio_gql-01").set_value("He now charges in non-biting currency.")
    at.number_input(key="edit_gql-01_0").set_value(99)
    at.button(key="FormSubmitter:edit_gql-01-Save card").click().run()
    assert not at.exception
    assert load_deck(path)[0].name == "Bixby the Revised"
    assert load_deck(path)[0].stats[0] == 99
    assert at.session_state.match.deck[0] == original
    at.switch_page("app_pages/play.py").run()
    assert at.session_state.match.deck[0] == original


def test_terminal_rematch_uses_latest_saved_deck(app):
    from guild.storage import update_card
    at, path = app
    deck = load_deck(path)
    match = new_match(deck, (Player("A"), Player("Ledger", True)), 2)
    at.session_state.match = replace(match, phase="finished", piles=(tuple(c.id for c in deck), ()), winner=0)
    update_card(replace(deck[0], name="A new legend"), path)
    at.run()
    at.button(key="rematch").click().run()
    assert not at.exception
    assert at.session_state.match.deck[0].name == "A new legend"
    assert at.session_state.match.round_number == 0
