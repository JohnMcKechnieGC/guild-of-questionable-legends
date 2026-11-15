# Verification

Verified locally on 15 November 2026 with Python 3.14, Streamlit 1.67.0, Pillow 12.3.0, pytest 9.2.0 and Playwright 1.65.2 / Chromium 159.

## Automated suite

`python -m pytest -q` — **44 passed in 9.06 seconds**.

- All three player counts: equal clockwise deals, random dealers, next-seat first choice, exactly one computer.
- Clear wins and deterministic collection order, including the winner's own card and existing pot.
- Consecutive highest-score ties: every played card enters the pot, every surviving player participates, and the stat stays locked.
- An eliminated chooser during a tie; a previous nonleader winning the eventual comparison.
- Empty seats excluded, sole survivor awarded the pot, all-empty house-rule draws for 2/3/4 players, normal all-36-card wins.
- Computer sampling: three distinct stats, highest sampled score, random equal-score selection; 6,000 seeded policy trials covering all 20 possible subsets. The policy accepts only its own card and a random generator.
- Card conservation checked after every transition, including up to 36,000 transitions across 24 seeded simulations. No turn cap or guaranteed-termination assumption is introduced into gameplay.
- Duplicate/stale actions, reruns during human and computer phases, and explicit result acknowledgments.
- Names, biographies, all six stats and image bytes saved to SQLite; validation failures remain atomic. Invalid numbers, names, missing IDs, corrupt images, and duplicate names are rejected.
- Database reopen in a separate Python process preserves edits. Startup cannot seed over the existing database. Triggers protect card count and stable IDs.
- Backup restoration produces the same deck. Match snapshots preserve old content; later matches and rematches see saved edits.
- Streamlit AppTest verifies actual forms, pass-screen privacy, reveals, results, computer actions, editor validation/save, navigation and rematches.

## Deck and artwork

`python scripts/audit_deck.py` — passed. Exactly 36 distinct characters, six integer stats per card and 36 distinct portrait BLOBs. All portraits decode at **600×800**. SQLite integrity check returns `ok`.

The [distribution audit](DECK_AUDIT.md) records category ranges, means, medians, repeated-value frequencies and every character's total, strength and weakness. Card totals span **160–510 / 600**. Thirty-five characters have a best-to-worst spread of at least 30. Equal-value pairs occur in every category (21–31 of 630 starting-deck pairs).

All 36 portraits were generated through Codex's built-in image tool using separate original prompts. Source images and the [prompt set](assets/ARTWORK.md) are included. The full contact sheet was visually inspected for consistent illustration style, distinct characters, fitting visual gags and absence of text, logos and baked-in card borders.

## Running app and real browser

`python scripts/browser_smoke.py` — passed against a launched localhost Streamlit server using a temporary copy of the deck.

- Read the running server's agent API protocol; loaded the app, dealt cards and drove turn transitions successfully.
- Chromium played four comparisons each in 2-, 3- and 4-player games, checking the human privacy gate, chooser-only card display and explicit result screens.
- Editor rejected a blank name, then saved a name, bio, stat and replacement portrait. The replacement decoded correctly and the edit persisted through a page reload.
- Downloaded a complete SQLite backup through the actual browser and verified that reopening it reproduced the saved deck.
- Checked desktop presentation and a 390px mobile viewport, with no page horizontal overflow or JavaScript errors.
- Blocked external HTTP requests throughout browser testing; no nonlocal requests were needed.
- Server console contained no warnings or tracebacks.

Screenshots, the deck contact sheet, agent API artifacts and server log are under `artifacts/` (ignored by version control). The regular app was also launched on **http://127.0.0.1:8501** with the original shipped deck. The test server was stopped after verification.

`ty check app.py guild app_pages scripts tests` — all checks passed. Python byte compilation also passed.

## Remaining limitations

No requested feature is incomplete. Matches are stored in browser-session state as requested and are not resumable after a server restart or a lost session; deck edits are persistent. There is no artificial round limit, so deals can take a long time or cycle under the specified rules. Testing verifies the transitions and conservation, rather than claiming every possible deal must terminate.
