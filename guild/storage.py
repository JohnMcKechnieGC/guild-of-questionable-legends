"""SQLite deck repository. Startup is read-only; seeding is an explicit tool."""
from contextlib import closing
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import sqlite3
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from guild.rules import Card

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "deck.sqlite3"
COLUMNS = ("weapon_skill", "strength", "toughness", "luck", "charisma", "intelligence")
MAX_UPLOAD = 8 * 1024 * 1024


def _decode_portrait(raw: bytes) -> Image.Image:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_UPLOAD:
        raise ValueError("Choose a PNG, JPEG or WebP portrait up to 8 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in ("PNG", "JPEG", "WEBP"):
                    raise ValueError("Portraits must be PNG, JPEG or WebP.")
                if image.width < 96 or image.height < 96 or image.width * image.height > 20_000_000:
                    raise ValueError("Portraits must be at least 96×96 and at most 20 megapixels.")
                image.load()
                return ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("The portrait could not be decoded safely.") from exc


def normalize_portrait(raw: bytes) -> bytes:
    with _decode_portrait(raw) as decoded:
        image = ImageOps.fit(decoded, (600, 800), method=Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, "WEBP", quality=90, method=6)
        return output.getvalue()


def validate_card(card: Card) -> Card:
    name, bio = card.name.strip(), card.bio.strip()
    if not 1 <= len(name) <= 80 or any(ord(c) < 32 for c in name):
        raise ValueError("Name must be 1–80 printable characters.")
    if not 1 <= len(bio) <= 600 or any(ord(c) < 32 and c not in "\n\t" for c in bio):
        raise ValueError("Biography must be 1–600 characters.")
    if len(card.stats) != 6 or any(type(v) is not int or not 1 <= v <= 100 for v in card.stats):
        raise ValueError("All six stats must be whole numbers from 1 to 100.")
    if not isinstance(card.portrait, bytes):
        raise ValueError("Portrait must contain image bytes.")
    return replace(card, name=name, bio=bio)


def _open(path: Path) -> sqlite3.Connection:
    # mode=rw refuses to silently create an empty replacement for a missing deck.
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=rw", uri=True, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def load_deck(path: Path = DEFAULT_DB) -> tuple[Card, ...]:
    with closing(_open(path)) as db:
        rows = db.execute("SELECT * FROM cards ORDER BY id").fetchall()
    deck = tuple(
        Card(
            r["id"],
            r["name"],
            r["bio"],
            tuple(r[c] for c in COLUMNS), bytes(r["portrait"])) for r in rows
    )
    if len(deck) != 36 or len({c.id for c in deck}) != 36:
        raise ValueError("The saved deck must contain exactly 36 cards.")
    return tuple(validate_card(c) for c in deck)


def update_card(card: Card, path: Path = DEFAULT_DB) -> None:
    card = validate_card(card)
    # Decode all incoming bytes before committing. Preserve normalized existing art.
    with _decode_portrait(card.portrait):
        pass
    with closing(_open(path)) as db, db:
        duplicate = db.execute(
            "SELECT id FROM cards WHERE name = ? COLLATE NOCASE AND id != ?",
            (card.name, card.id)
        ).fetchone()
        if duplicate:
            raise ValueError("Another character already has that name.")
        cursor = db.execute(
            "UPDATE cards SET name=?, bio=?, weapon_skill=?, strength=?, toughness=?, luck=?, charisma=?, intelligence=?, portrait=? WHERE id=?",
            (card.name, card.bio, *card.stats, sqlite3.Binary(card.portrait), card.id)
        )
        if cursor.rowcount != 1:
            raise ValueError("That stable card ID does not exist.")


def backup_bytes(path: Path = DEFAULT_DB) -> bytes:
    with closing(_open(path)) as source, closing(sqlite3.connect(":memory:")) as target:
        source.backup(target)
        return target.serialize()


def create_deck(cards: tuple[Card, ...], path: Path) -> None:
    """Explicit developer import. Never replace an existing file."""
    if len(cards) != 36 or len({c.id for c in cards}) != 36:
        raise ValueError("Exactly 36 unique stable IDs are required.")
    cards = tuple(validate_card(c) for c in cards)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb"):
        pass
    try:
        with closing(sqlite3.connect(path)) as db, db:
            stats_sql = ", ".join(f"{c} INTEGER NOT NULL CHECK(typeof({c})='integer' AND {c} BETWEEN 1 AND 100)" for c in COLUMNS)
            db.execute(
                f"CREATE TABLE cards (id TEXT PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(trim(name)) BETWEEN 1 AND 80), bio TEXT NOT NULL CHECK(length(trim(bio)) BETWEEN 1 AND 600), {stats_sql}, portrait BLOB NOT NULL CHECK(typeof(portrait)='blob' AND length(portrait)>0))")
            db.executemany("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?)", [(c.id, c.name, c.bio, *c.stats, sqlite3.Binary(c.portrait)) for c in cards])
            db.executescript("""
                CREATE TRIGGER fixed_count_insert BEFORE INSERT ON cards BEGIN SELECT RAISE(ABORT, 'Deck is fixed at 36 cards'); END;
                CREATE TRIGGER fixed_count_delete BEFORE DELETE ON cards BEGIN SELECT RAISE(ABORT, 'Deck is fixed at 36 cards'); END;
                CREATE TRIGGER stable_ids BEFORE UPDATE OF id ON cards BEGIN SELECT RAISE(ABORT, 'Stable IDs cannot change'); END;
                PRAGMA user_version=1;
            """)
    except Exception:
        path.unlink(missing_ok=True)
        raise
