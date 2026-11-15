from collections import Counter
from dataclasses import replace
import random

import pytest

from guild.rules import (Card, Match, Player, act, assert_conserved,
                         choose_computer_stat, new_match)


@pytest.fixture
def deck():
    return tuple(Card(f"c{i}", f"Misfit {i}", "A testing legend.", (50,) * 6, b"") for i in range(36))


def rig(deck, piles, values, chooser=0, phase="choose"):
    cards = tuple(replace(c, stats=(values.get(i, 50),) * 6) for i, c in enumerate(deck))
    used = {i for pile in piles for i in pile}
    match = Match(cards, tuple(Player(f"Seat {i}", i == len(piles) - 1) for i in range(len(piles))),
                  tuple(tuple(f"c{i}" for i in p) for p in piles),
                  tuple(f"c{i}" for i in range(36) if i not in used), 0, chooser, phase,
                  random.Random(42).getstate())
    assert_conserved(match)
    return match


def do(match, action, stat=None):
    result = act(match, action, match.revision, stat)
    assert_conserved(result)
    return result


@pytest.mark.parametrize("count", [2, 3, 4])
def test_equal_deal_clockwise_and_random_dealer(deck, count):
    players = tuple(Player(str(i), i == count - 1) for i in range(count))
    dealers = set()
    for seed in range(30):
        match = new_match(deck, players, seed)
        assert [len(p) for p in match.piles] == [36 // count] * count
        assert match.chooser == (match.dealer + 1) % count
        assert match.phase == ("computer" if players[match.chooser].computer else "pass")
        assert match == new_match(deck, players, seed)
        rng = random.Random(seed)
        shuffled = [c.id for c in deck]
        rng.shuffle(shuffled)
        assert match.piles[match.chooser][0] == shuffled[0]
        assert_conserved(match)
        dealers.add(match.dealer)
    assert dealers == set(range(count))


@pytest.mark.parametrize("players", [(Player("a"),), (Player("a"), Player("b")), (Player("a", True), Player("b", True)), (Player("a"), Player("a", True))])
def test_invalid_players(deck, players):
    with pytest.raises(ValueError):
        new_match(deck, players)


def test_clear_win_own_card_and_order(deck):
    match = rig(deck, [[0, 1], [2, 3], [4, 5]], {0: 30, 2: 95, 4: 70})
    old_pot = match.pot
    result = do(match, "choose", 0)
    assert result.chooser == 1
    assert result.piles[1] == ("c3", "c0", "c2", "c4") + old_pot
    assert not result.pot
    assert result.result.winner == 1
    assert result.phase == "result"
    assert do(result, "continue").phase == "pass"


def test_consecutive_ties_include_everyone_and_lock_stat(deck):
    match = rig(deck, [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
                {0: 90, 3: 90, 6: 20, 1: 80, 4: 80, 7: 10, 2: 20, 5: 20, 8: 95})
    first = do(match, "choose", 4)
    assert first.pot[-3:] == ("c0", "c3", "c6")
    second = do(do(first, "continue"), "tie")
    assert second.pot[-3:] == ("c1", "c4", "c7")
    assert second.locked_stat == 4
    assert len(second.result.played) == 3
    third = do(do(second, "continue"), "tie")
    assert third.result.winner == 2  # neither of the earlier tied leaders
    assert len(third.piles[2]) == 36 and not third.pot
    assert do(third, "continue").phase == "finished"


def test_chooser_eliminated_during_tie(deck):
    match = rig(deck, [[0], [1, 2, 3], [4, 5, 6]], {0: 80, 1: 80, 4: 20, 2: 10, 5: 90})
    first = do(match, "choose", 2)
    assert first.piles[0] == () and first.chooser == 0
    locked = do(first, "continue")
    assert do(locked, "computer") is locked  # no fresh computer choice in a tie
    second = do(locked, "tie")
    assert [p[0] for p in second.result.played] == [1, 2]
    assert second.result.stat == 2 and second.chooser == 2
    assert second.piles[0] == ()


def test_only_survivor_awarded_pot(deck):
    match = rig(deck, [[0], [1, 2]], {0: 70, 1: 70})
    result = do(match, "choose", 1)
    assert result.winner == 1 and len(result.piles[1]) == 36
    assert not result.pot and result.result.terminal


@pytest.mark.parametrize("count", [2, 3, 4])
def test_all_empty_tie_house_rule_draw(deck, count):
    match = rig(deck, [[i] for i in range(count)], {})
    result = do(match, "choose", 0)
    assert result.draw and result.winner is None
    assert len(result.pot) == 36 and all(not p for p in result.piles)
    assert "House rule" in result.result.message
    assert do(result, "continue").phase == "finished"


def test_clear_final_win_and_eliminated_seat_skipped(deck):
    result = do(rig(deck, [[0], [], [1]], {0: 100, 1: 10}), "choose", 0)
    assert result.winner == 0 and len(result.piles[0]) == 36
    assert len(result.result.played) == 2


def test_rerun_and_duplicate_events_are_noops(deck):
    match = rig(deck, [[0, 1], [2, 3]], {0: 90, 2: 10})
    result = do(match, "choose", 0)
    assert act(result, "choose", match.revision, 0) is result
    assert act(result, "choose", result.revision, 0) is result
    next_turn = do(result, "continue")
    assert act(next_turn, "continue", result.revision) is next_turn


def test_computer_exact_policy_and_random_tie_break(deck):
    card = replace(deck[0], stats=(10, 20, 30, 40, 50, 60))
    samples = Counter()
    equal_choices = Counter()
    for seed in range(6000):
        stat, sampled = choose_computer_stat(card, random.Random(seed))
        assert len(set(sampled)) == 3 and stat in sampled
        assert card.stats[stat] == max(card.stats[i] for i in sampled)
        samples[tuple(sorted(sampled))] += 1
        equal_choices[choose_computer_stat(deck[0], random.Random(seed))[0]] += 1
    assert len(samples) == 20
    assert all(220 < count < 380 for count in samples.values())
    assert all(850 < count < 1150 for count in equal_choices.values())


def test_computer_turn_once_and_reproducible(deck):
    match = rig(deck, [[0, 1], [2, 3]], {0: 20, 2: 90}, chooser=1, phase="computer")
    result = do(match, "computer")
    assert result == do(match, "computer")
    assert len(result.sampled) == 3
    assert act(result, "computer", match.revision) is result
    assert do(do(result, "continue"), "computer").round_number == 2


@pytest.mark.parametrize("count", [2, 3, 4])
def test_card_conservation_through_long_play(deck, count):
    varied = tuple(replace(c, stats=tuple(5 + ((i * 17 + s * 13) % 19) * 5 for s in range(6))) for i, c in enumerate(deck))
    for seed in range(8):
        match = new_match(varied, tuple(Player(str(i), i == count - 1) for i in range(count)), seed)
        rng = random.Random(seed)
        for _ in range(1500):
            assert_conserved(match)
            if match.phase == "finished":
                break
            action = {"pass": "reveal", "choose": "choose", "computer": "computer", "tie": "tie", "result": "continue"}[match.phase]
            match = do(match, action, rng.randrange(6) if action == "choose" else None)
        if match.phase == "finished":
            assert match.draw or max(map(len, match.piles)) == 36
