"""Explicit one-time art import; refuses to overwrite a saved deck."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from guild.rules import Card
from guild.storage import DEFAULT_DB, create_deck, normalize_portrait


if __name__ == "__main__":
    source = json.loads((ROOT / "assets/deck.json").read_text(encoding="utf-8"))
    cards = tuple(Card(c["id"], c["name"], c["bio"], tuple(c["stats"]),
                       normalize_portrait((ROOT / "assets/portraits" / (c["id"] + ".png")).read_bytes())) for c in source)
    create_deck(cards, Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB)
    print(f"Imported {len(cards)} cards, including image BLOBs.")
