"""Pure game transitions. No UI, storage, network or hidden opponent inspection."""
from collections import Counter
from dataclasses import dataclass, replace
import random

STATS = ("Weapon Skill", "Strength", "Toughness", "Luck", "Charisma", "Intelligence")


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    bio: str
    stats: tuple[int, ...]
    portrait: bytes


@dataclass(frozen=True)
class Player:
    name: str
    computer: bool = False


@dataclass(frozen=True)
class Result:
    number: int
    stat: int
    played: tuple[tuple[int, str, int], ...]
    winner: int | None
    tied: bool
    collected: int
    message: str
    terminal: bool = False


@dataclass(frozen=True)
class Match:
    deck: tuple[Card, ...]
    players: tuple[Player, ...]
    piles: tuple[tuple[str, ...], ...]
    pot: tuple[str, ...]
    dealer: int
    chooser: int
    phase: str
    rng_state: tuple
    locked_stat: int | None = None
    result: Result | None = None
    round_number: int = 0
    revision: int = 0
    winner: int | None = None
    draw: bool = False
    sampled: tuple[int, ...] = ()

    def card(self, card_id: str) -> Card:
        return next(c for c in self.deck if c.id == card_id)


def assert_conserved(match: Match) -> None:
    expected = Counter(c.id for c in match.deck)
    actual = Counter(c for pile in match.piles for c in pile) + Counter(match.pot)
    assert len(expected) == 36 and all(v == 1 for v in expected.values())
    assert actual == expected, "A card was lost, duplicated, or invented"


def new_match(deck: tuple[Card, ...], players: tuple[Player, ...], seed=None) -> Match:
    if len(players) not in (2, 3, 4) or sum(p.computer for p in players) != 1:
        raise ValueError("Use 2–4 players with exactly one computer.")
    names = [p.name.strip().casefold() for p in players]
    if any(not n or len(n) > 30 for n in names) or len(set(names)) != len(names):
        raise ValueError("Player names must be distinct and 1–30 characters long.")
    if len(deck) != 36 or len({c.id for c in deck}) != 36:
        raise ValueError("The deck must contain exactly 36 distinct cards.")
    rng = random.Random(seed)
    ids = [c.id for c in deck]
    rng.shuffle(ids)
    dealer = rng.randrange(len(players))
    chooser = (dealer + 1) % len(players)
    piles: list[list[str]] = [[] for _ in players]
    for i, card_id in enumerate(ids):
        piles[(chooser + i) % len(players)].append(card_id)
    match = Match(tuple(deck), players, tuple(tuple(p) for p in piles), (), dealer,
                  chooser, "computer" if players[chooser].computer else "pass", rng.getstate())
    assert_conserved(match)
    return match


def choose_computer_stat(card: Card, rng: random.Random) -> tuple[int, tuple[int, ...]]:
    """Only the computer's own card is an input. Uniform 3-of-6 sample."""
    sampled = tuple(rng.sample(range(6), 3))
    best = max(card.stats[i] for i in sampled)
    return rng.choice([i for i in sampled if card.stats[i] == best]), sampled


def _compare(match: Match, stat: int) -> Match:
    piles = [list(p) for p in match.piles]
    played = tuple((seat, pile.pop(0), 0) for seat, pile in enumerate(piles) if pile)
    played = tuple((seat, cid, match.card(cid).stats[stat]) for seat, cid, _ in played)
    high = max(value for _, _, value in played)
    leaders = [seat for seat, _, value in played if value == high]
    cards = tuple(cid for _, cid, _ in played)
    pot = match.pot
    tied = len(leaders) > 1
    winner = None
    collected = 0
    terminal = False
    draw = False
    chooser = match.chooser
    if tied:
        pot += cards
        survivors = [i for i, p in enumerate(piles) if p]
        if not survivors:
            terminal = draw = True
            message = "Draw — everyone ran out on the same tied comparison. House rule: leave the cards in the pot and offer a rematch."
        elif len(survivors) == 1:
            winner = chooser = survivors[0]
            collected = len(pot)
            piles[winner].extend(pot)
            pot = ()
            terminal = True
            message = f"{match.players[winner].name} is the only player with cards and collects the entire pot."
        else:
            message = f"Tied at {high}. Every played card enters the pot. {STATS[stat]} stays locked; all players with cards compare again."
    else:
        winner = chooser = leaders[0]
        collected = len(cards) + len(pot)
        # Fixed clockwise seat order starting at seat 1, then old pot oldest first.
        piles[winner].extend(cards + pot)
        pot = ()
        terminal = sum(bool(p) for p in piles) == 1
        message = f"{match.players[winner].name} wins with {high} and collects {collected} cards."
    if terminal and not draw:
        assert winner is not None
        message += f" {match.players[winner].name} holds all 36 cards and wins the match!"
    result = Result(match.round_number + 1, stat, played, winner, tied, collected, message, terminal)
    updated = replace(match, piles=tuple(tuple(p) for p in piles), pot=pot, chooser=chooser,
                      phase="result", locked_stat=stat if tied and not terminal else None,
                      result=result, round_number=result.number, winner=winner if terminal else None,
                      draw=draw, revision=match.revision + 1)
    assert_conserved(updated)
    return updated


def act(match: Match, action: str, expected_revision: int, stat: int | None = None) -> Match:
    """Stale UI events are no-ops; every accepted event consumes one revision."""
    if expected_revision != match.revision:
        return match
    if action == "reveal" and match.phase == "pass":
        return replace(match, phase="choose", revision=match.revision + 1)
    if action == "choose" and match.phase == "choose":
        if type(stat) is not int or stat not in range(6):
            raise ValueError("Choose one of the six stats.")
        return _compare(match, stat)
    if action == "computer" and match.phase == "computer":
        rng = random.Random()
        rng.setstate(match.rng_state)
        chosen, sampled = choose_computer_stat(match.card(match.piles[match.chooser][0]), rng)
        return _compare(replace(match, sampled=sampled, rng_state=rng.getstate()), chosen)
    if action == "tie" and match.phase == "tie":
        assert match.locked_stat is not None
        return _compare(match, match.locked_stat)
    if action == "continue" and match.phase == "result":
        assert match.result is not None
        phase = "finished" if match.result.terminal else (
            "tie" if match.locked_stat is not None else
            "computer" if match.players[match.chooser].computer else "pass")
        return replace(match, phase=phase, result=None, sampled=(), revision=match.revision + 1)
    return match
