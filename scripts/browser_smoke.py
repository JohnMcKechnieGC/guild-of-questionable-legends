"""Real localhost app/API and Chromium smoke test; never edits the shipped deck."""
from contextlib import closing
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from guild.storage import DEFAULT_DB, load_deck


def request(url, payload=None):
    req = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def main():
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="guild-smoke-") as tmp:
        database = Path(tmp) / "deck.sqlite3"
        shutil.copyfile(DEFAULT_DB, database)
        with closing(socket.socket()) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = dict(os.environ, GUILD_DB_PATH=str(database), PYTHONUTF8="1")
        with (artifacts / "smoke-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py",
                                       "--server.headless=true", f"--server.port={port}",
                                       "--server.enableAgentApi=true"], cwd=ROOT, env=env,
                                      stdout=log, stderr=subprocess.STDOUT,
                                      creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                for _ in range(100):
                    try:
                        with urlopen(base + "/_stcore/health", timeout=1) as response:
                            if response.read() == b"ok":
                                break
                    except OSError:
                        if server.poll() is not None:
                            raise RuntimeError("Streamlit exited; see smoke-server.log")
                        time.sleep(.1)
                else:
                    raise RuntimeError("Streamlit did not become healthy")
                protocol = request(base + "/_stcore/agent/openapi.json")
                (artifacts / "agent-openapi.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
                state = request(base + "/_stcore/agent/interact", {})
                assert state["status"] == "ready", state
                sid = state["session_id"]
                state = request(base + "/_stcore/agent/interact", {"session_id": sid, "trigger": {"key": "FormSubmitter:new_game-Shuffle & deal"}})
                assert state["status"] == "ready", state
                for _ in range(5):
                    keys = {a["key"] for a in state["actions"]}
                    key = next(k for k in ("reveal", "stat_0", "computer", "tie", "continue") if k in keys)
                    state = request(base + "/_stcore/agent/interact", {"session_id": sid, "trigger": {"key": key}})
                    assert state["status"] == "ready", state
                (artifacts / "agent-snapshot.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
                print("Live agent API: healthy, protocol read, deal and turn transitions passed.")

                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    context = browser.new_context(viewport={"width": 1440, "height": 1050})
                    # Block nonlocal requests to exercise offline gameplay.
                    external = []
                    def route_request(route):
                        if route.request.url.startswith((base, "data:", "blob:")):
                            route.continue_()
                        else:
                            external.append(route.request.url)
                            route.abort()
                    context.route("**/*", route_request)
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    for count in (2, 3, 4):
                        if count != 2:
                            page.close()
                            page = context.new_page()
                            page.on("pageerror", lambda error: errors.append(str(error)))
                        page.goto(base)
                        page.get_by_role("button", name="Shuffle & deal", exact=True).wait_for()
                        if count != 2:
                            page.get_by_role("radio", name=str(count), exact=True).click()
                        page.get_by_label(f"Human {count - 1}", exact=True).wait_for()
                        if count == 2:
                            page.screenshot(path=str(artifacts / "lobby.png"), full_page=True)
                        page.get_by_role("button", name="Shuffle & deal", exact=True).click()
                        page.get_by_text("Cards accounted for: 36 / 36", exact=False).wait_for()
                        comparisons = 0
                        while comparisons < 4:
                            page.get_by_role("button", name=re.compile(r"^(I'm ready|Weapon Skill ·|Let Ledger call a stat|Reveal next cards)")).first.wait_for()
                            page.get_by_test_id("stStatusWidget").wait_for(state="hidden")
                            if page.get_by_role("button", name="I'm ready — reveal my card", exact=True).count():
                                assert page.locator('[data-testid="stImage"]').count() == 0
                                page.get_by_role("button", name="I'm ready — reveal my card", exact=True).click()
                                page.get_by_role("button", name="Weapon Skill ·", exact=False).wait_for()
                            human = page.get_by_role("button", name="Weapon Skill ·", exact=False)
                            computer = page.get_by_role("button", name="Let Ledger call a stat", exact=True)
                            tie = page.get_by_role("button", name="Reveal next cards", exact=True)
                            if human.count():
                                assert page.locator('[data-testid="stImage"]').count() == 1
                                human.click()
                            elif computer.count():
                                assert page.locator('[data-testid="stImage"]').count() == 1
                                computer.click()
                            elif tie.count():
                                tie.click()
                            else:
                                raise AssertionError("No legal comparison action: " + page.locator("body").aria_snapshot())
                            page.get_by_role("heading", name="Round result ·", exact=False).wait_for()
                            page.get_by_role("button", name="Continue", exact=True).wait_for()
                            assert 2 <= page.locator('[data-testid="stImage"]').count() <= count
                            assert page.locator('[data-testid="stException"]').count() == 0
                            if comparisons == 0:
                                page.screenshot(path=str(artifacts / f"result-{count}-players.png"), full_page=True)
                            page.get_by_role("button", name="Continue", exact=True).click()
                            page.get_by_role("heading", name="Round result ·", exact=False).wait_for(state="detached")
                            comparisons += 1
                        print(f"Chromium: {count}-player deal, privacy gate and four comparisons passed.")
                    page.get_by_role("link", name="Deck Editor", exact=True).click()
                    page.get_by_role("button", name="Save card", exact=True).wait_for()
                    before = load_deck(database)[0]
                    page.get_by_label("Name", exact=True).fill(" ")
                    page.get_by_role("button", name="Save card", exact=True).click()
                    page.get_by_text("Name must be 1–80 printable characters.", exact=True).wait_for()
                    assert load_deck(database)[0] == before
                    page.get_by_label("Name", exact=True).fill("Bixby Browserchecked")
                    page.get_by_label("Biography", exact=True).fill("His buttons passed their browser inspection.")
                    page.get_by_role("spinbutton", name="Weapon Skill", exact=True).fill("99")
                    page.locator('input[type="file"]').set_input_files(str(ROOT / "assets/portraits/gql-02.png"))
                    page.get_by_text("gql-02.png", exact=True).wait_for()
                    page.get_by_role("button", name="Save card", exact=True).click()
                    page.get_by_text("Card saved. The next match will use your changes.", exact=True).wait_for()
                    after = load_deck(database)[0]
                    assert after.name == "Bixby Browserchecked" and after.stats[0] == 99
                    assert after.portrait != before.portrait
                    with Image.open(BytesIO(after.portrait)) as image:
                        image.load()
                        assert image.size == (600, 800)
                    page.screenshot(path=str(artifacts / "editor.png"), full_page=True)
                    with page.expect_download() as download_event:
                        page.get_by_role("button", name="Download deck backup", exact=True).click()
                    backup = Path(tmp) / "download.sqlite3"
                    download_event.value.save_as(backup)
                    assert load_deck(backup) == load_deck(database)
                    page.reload()
                    page.get_by_label("Name", exact=True).wait_for()
                    assert page.get_by_label("Name", exact=True).input_value() == "Bixby Browserchecked"
                    page.close()
                    page = context.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.goto(base + "/editor")
                    page.get_by_role("button", name="Save card", exact=True).wait_for()
                    page.screenshot(path=str(artifacts / "editor-mobile.png"), full_page=True)
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                    assert not errors, errors
                    assert not external, external
                    browser.close()
                    print("Chromium: editor validation, name/bio/stat/portrait save, reload, backup restore, mobile layout and offline requests passed.")
            finally:
                server.terminate()
                server.wait(timeout=15)
        log_text = (artifacts / "smoke-server.log").read_text(encoding="utf-8")
        assert "Traceback" not in log_text, log_text
        print("Server console: no tracebacks. Smoke test complete.")


if __name__ == "__main__":
    main()
