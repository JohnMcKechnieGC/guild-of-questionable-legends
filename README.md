# Guild of Questionable Legends

A complete local fantasy card game for **2–4 players, exactly one computer**. One to three humans pass a shared screen/keyboard. Thirty-six original misfits compete across six talents, with a central pot that grows whenever the highest score is tied.

## Run locally

Use Python 3.11 or newer. From this project directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. On macOS/Linux, activate with `source .venv/bin/activate`.

The populated database is **`data/deck.sqlite3`**. No seed command is needed. Once Python dependencies are installed, gameplay, portraits, editing and backups need no internet, image service or API key. The server binds to the local machine; there are no accounts or online opponents.

## Play

Choose two, three or four total players, enter the human names and press **Shuffle & deal**. The last seat belongs to **Ledger**, the computer. Follow the pass-screen prompt before revealing a human's top card. Call a stat, read the round result, then continue. Ledger also acts only when its action button is pressed.

All six stats are integers from 1–100, and higher is always better. Clear winners take all played cards and the pot. Ties put every played card in the pot and lock the stat; **all players with cards compare again**, including those who lost the previous comparison. Empty piles are eliminated. A sole survivor receives the pot. **House rule:** if all piles empty on the same tied comparison, the game is a draw and offers a rematch. Otherwise, collecting all 36 cards wins.

The dealer is random, the next clockwise seat chooses first, and equal piles contain 18, 12 or 9 cards. Captures are appended in fixed seat order starting at seat 1, then the previous pot in oldest-first order. Ledger uniformly samples three distinct stats from its own card, calls the highest and breaks equal scores randomly. It never chooses again within a tie.

Read the complete [rules](RULES.md). There is no automatic turn limit: some deals can be long or cycle. Use **Leave this match** to return to the tavern. Matches live in Streamlit session state: ordinary reruns preserve them, while a server restart or a lost browser session can discard them. Deck edits are saved permanently.

## Edit and back up the deck

Open **Deck Editor** in the sidebar, select a character and update the name, biography or six stats. Upload a PNG, JPEG or WebP to replace its portrait. Images must be 96×96 or larger, at most 20 megapixels and at most 8 MB; the editor center-crops them to 600×800. Press **Save card**. Blank names/bios, duplicate names and stats outside 1–100 are rejected before committing.

Names may contain 1–80 characters; bios may contain 1–600. Stable IDs and the count of 36 are protected by database triggers. There are no add/delete controls. New matches and rematches use the latest saved database. Ongoing matches hold immutable copies of the original card data, including image bytes.

**Download deck backup** saves a consistent SQLite database containing all card data and portrait BLOBs. To restore: stop Streamlit, keep a copy of your current database, replace `data/deck.sqlite3` with the backup, then restart. You can also copy that file directly while the app is stopped. Startup never seeds, resets or overwrites a deck. A missing database produces an error rather than creating an empty one.

## Verify

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/audit_deck.py
```

Tests cover all player counts, equal clockwise deals, clear wins and collection order, repeated ties involving nonleaders, chooser elimination, sole survivors, all-empty draws, final wins, stale events, the computer policy, thousands of conservation checks, database constraints, backups, edits surviving a separate Python process, match snapshots and Streamlit widget flows. Test writes use temporary copies of the database.

The audit decodes all 36 portrait BLOBs, checks uniqueness and crop, creates `artifacts/deck-contact-sheet.jpg`, and writes [stat distributions](DECK_AUDIT.md). Statistics describe the authored starting deck; edited decks can change the balance.

For a real Chromium smoke test (including image upload and a downloaded SQLite backup):

```powershell
python -m playwright install chromium
python scripts/browser_smoke.py
```

It starts its own localhost server using a temporary deck, checks 2–4 player flows and the editor, saves screenshots under `artifacts/`, then stops that server. See [verification results](VERIFICATION.md) for the development run.

## Project layout

- `guild/rules.py`: pure immutable match state and transitions; no Streamlit or SQLite.
- `guild/storage.py`: validation, SQLite repository, one-time importer and backup.
- `guild/interface.py`, `app.py`, `app_pages/`: shared session callbacks and Streamlit pages.
- `data/deck.sqlite3`: the live, populated 36-card deck, including actual portrait bytes.
- `assets/deck.json`, `assets/portraits/`: original authoring data and AI-generated source artwork. Runtime uses the database, so changing these files does not overwrite saved edits.
- `scripts/build_deck.py`: explicit development importer; refuses to replace an existing database. To build a separate fresh copy, run `python scripts/build_deck.py data/fresh.sqlite3`.
- `tests/`: rules, database and Streamlit regression tests.

Artwork was generated during development using Codex's built-in image-generation capability, one original prompt per character. The [artwork notes and prompt set](assets/ARTWORK.md) document the sources. No runtime image generation is used.
