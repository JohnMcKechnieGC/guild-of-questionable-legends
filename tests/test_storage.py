from dataclasses import replace
from io import BytesIO
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

from PIL import Image
import pytest

from guild.rules import Player, new_match
from guild.storage import (DEFAULT_DB, backup_bytes, load_deck,
                           normalize_portrait, update_card, create_deck)


@pytest.fixture
def saved_deck(tmp_path):
    path = tmp_path / "deck.sqlite3"
    shutil.copyfile(DEFAULT_DB, path)
    return path


def test_complete_deck_and_portraits():
    deck = load_deck()
    assert len(deck) == len({c.name for c in deck}) == 36
    assert len({c.portrait for c in deck}) == 36
    for card in deck:
        assert len(card.stats) == 6
        assert all(type(s) is int and 1 <= s <= 100 for s in card.stats)
        with Image.open(BytesIO(card.portrait)) as image:
            image.load()
            assert image.size == (600, 800)
    with sqlite3.connect(DEFAULT_DB) as db:
        assert db.execute("SELECT count(*) FROM cards WHERE typeof(portrait)='blob'").fetchone()[0] == 36
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_edit_survives_process_restart_and_snapshot(saved_deck):
    original = load_deck(saved_deck)
    match = new_match(original, (Player("A"), Player("Ledger", True)), 1)
    raw = BytesIO()
    Image.new("RGB", (140, 200), "coral").save(raw, "PNG")
    edited = replace(original[0], name="Quartermaster Revised", bio="The buttons have unionized.", stats=(1, 22, 33, 44, 55, 100), portrait=normalize_portrait(raw.getvalue()))
    update_card(edited, saved_deck)
    assert load_deck(saved_deck)[0] == edited
    result = subprocess.run([sys.executable, "-c", "from pathlib import Path; import sys; from guild.storage import load_deck; c=load_deck(Path(sys.argv[1]))[0]; assert c.name == 'Quartermaster Revised'; assert c.stats == (1,22,33,44,55,100); print('persistent')", str(saved_deck)], capture_output=True, text=True, check=True)
    assert "persistent" in result.stdout
    assert match.deck[0] == original[0]
    assert new_match(load_deck(saved_deck), match.players, 1).deck[0] == edited
    with pytest.raises(FileExistsError):
        create_deck(original, saved_deck)
    assert load_deck(saved_deck)[0] == edited


@pytest.mark.parametrize("change", [{"name": " "}, {"bio": ""}, {"stats": (0, 2, 3, 4, 5, 6)}, {"stats": (1, 2, 3, 4, 5, 101)}, {"stats": (1.5, 2, 3, 4, 5, 6)}, {"stats": (True, 2, 3, 4, 5, 6)}, {"stats": (1, 2)}, {"id": "missing"}, {"portrait": b"not an image"}])
def test_invalid_edits_atomic(saved_deck, change):
    before = load_deck(saved_deck)
    with pytest.raises(ValueError):
        update_card(replace(before[0], **change), saved_deck)
    assert load_deck(saved_deck) == before


def test_duplicate_names_and_fixed_count(saved_deck):
    cards = load_deck(saved_deck)
    with pytest.raises(ValueError):
        update_card(replace(cards[0], name=cards[1].name.lower()), saved_deck)
    with sqlite3.connect(saved_deck) as db:
        for statement in ("DELETE FROM cards", "INSERT INTO cards SELECT * FROM cards", "UPDATE cards SET id='different' WHERE id='gql-01'", "UPDATE cards SET luck=0"):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(statement)
    assert len(load_deck(saved_deck)) == 36


def test_backup_can_be_restored(saved_deck, tmp_path):
    restored = tmp_path / "restored.sqlite3"
    restored.write_bytes(backup_bytes(saved_deck))
    assert load_deck(restored) == load_deck(saved_deck)


@pytest.mark.parametrize("raw", [b"", b"not an image", b"x" * (8 * 1024 * 1024 + 1)])
def test_bad_portrait_rejected(raw):
    with pytest.raises(ValueError):
        normalize_portrait(raw)


def test_missing_database_is_not_created(tmp_path):
    missing = tmp_path / "missing.sqlite3"
    with pytest.raises(sqlite3.OperationalError):
        load_deck(missing)
    assert not missing.exists()
