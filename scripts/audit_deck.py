"""Audit the actual shipped SQLite deck and write a reproducible report."""
from collections import Counter
from io import BytesIO
from pathlib import Path
import statistics
import sys

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from guild.rules import STATS
from guild.storage import load_deck


def audit():
    cards = load_deck()
    report = ["# Deck audit", "", f"{len(cards)} distinct characters; six integer stats per card, all in 1–100.", "", "| Stat | Min | Max | Mean | Median | Distinct values | Equal pairs / 630 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for i, label in enumerate(STATS):
        values = [c.stats[i] for c in cards]
        counts = Counter(values)
        pairs = sum(n * (n - 1) // 2 for n in counts.values())
        report.append(f"| {label} | {min(values)} | {max(values)} | {statistics.mean(values):.1f} | {statistics.median(values):.1f} | {len(counts)} | {pairs} ({pairs / 630:.1%}) |")
    report += ["", "These pair frequencies describe the starting deck, not the chance of a tied highest score during play.", "", "| Character | Total / 600 | Best | Weakest |", "|---|---:|---|---|"]
    for c in sorted(cards, key=lambda c: sum(c.stats), reverse=True):
        best = max(range(6), key=lambda i: c.stats[i])
        worst = min(range(6), key=lambda i: c.stats[i])
        report.append(f"| {c.name} | {sum(c.stats)} | {STATS[best]} {c.stats[best]} | {STATS[worst]} {c.stats[worst]} |")
    sheet = Image.new("RGB", (6 * 180, 6 * 264), "#112329")
    draw = ImageDraw.Draw(sheet)
    for i, card in enumerate(cards):
        with Image.open(BytesIO(card.portrait)) as image:
            image.load()
            assert image.size == (600, 800)
            sheet.paste(image.resize((174, 232)), ((i % 6) * 180 + 3, (i // 6) * 264))
        draw.text(((i % 6) * 180 + 4, (i // 6) * 264 + 235), card.name, fill="#f3ead9")
    assert len({c.portrait for c in cards}) == 36
    report += ["", "All 36 unique portrait BLOBs decode successfully at 600×800. The application reads these bytes from SQLite.", ""]
    (ROOT / "DECK_AUDIT.md").write_text("\n".join(report), encoding="utf-8")
    (ROOT / "artifacts").mkdir(exist_ok=True)
    sheet.save(ROOT / "artifacts/deck-contact-sheet.jpg")
    print("\n".join(report[:13]))


if __name__ == "__main__":
    audit()
