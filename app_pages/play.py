from random import choice
import streamlit as st

from guild.interface import (action_button, current_deck, leave_match, portrait,
                             start_match)
from guild.rules import Player, STATS, assert_conserved

st.caption("THE MOST DUBIOUS COMPANY IN THE REALM")
st.title("Guild of Questionable Legends")
match = st.session_state.match

if match is None:
    left, right = st.columns([1, 1.5], gap="large")
    with left:
        card = current_deck()[0]
        portrait(card, width=360)
        st.caption(f"Meet {card.name}. Even the paperwork is cursed.")

    with right:
        st.header("Greatness is a relative stat.")
        st.markdown("Outwit your friends, outlast the guild's computer, and collect all **36 cards**. Choose a "
                    "talent. Reveal the competition. Let the questionable legends speak for themselves.")
        total = st.segmented_control("Players at the table", [2, 3, 4], default=2, key="player_count") or 2

        with st.form("new_game"):
            names = [st.text_input(f"Human {i + 1}", value=f"Adventurer {i + 1}", max_chars=30, key=f"human_{i}") for i in range(total - 1)]
            st.caption("Final seat: Ledger, the computer. Seats run clockwise in the order shown.")

            if st.form_submit_button("Shuffle & deal", type="primary", width="stretch"):
                players = tuple(Player(n.strip()) for n in names) + (Player("Ledger", True),)
                start_match(players, st.session_state.match_serial)

                if st.session_state.match is not None:
                    st.rerun()

        if st.session_state.ui_error:
            st.error(st.session_state.ui_error)

        st.caption("Pass one screen/keyboard between humans. No account, connection, or magic subscription required.")

else:
    assert_conserved(match)
    serial = st.session_state.match_serial
    with st.container(horizontal=True):
        st.badge(f"Comparison {match.round_number + (match.phase not in ('result', 'finished'))}", icon=":material/swords:")
        st.badge(f"Pot: {len(match.pot)} cards", icon=":material/inventory_2:")
        if match.phase != "finished":
            st.badge(f"Chooser: {match.players[match.chooser].name}", color="orange")

    counts = st.columns(len(match.players))
    for seat, column in enumerate(counts):
        with column:
            count = len(match.piles[seat])
            st.metric(f"Seat {seat + 1} · {match.players[seat].name}", f"{count} cards", border=True)
            st.caption("Eliminated" if not count else "Computer" if match.players[seat].computer else "Human")

    st.divider()

    if match.phase == "pass":
        with st.container(border=True):
            st.header(f"Pass the screen/keyboard to {match.players[match.chooser].name}", anchor=False)
            action_button("I'm ready — reveal my card", "reveal", "reveal", primary=True)

    elif match.phase in ("choose", "computer"):
        card = match.card(match.piles[match.chooser][0])
        left, right = st.columns([1, 1.5], gap="large")
        with left:
            portrait(card, width=360)
        with right:
            st.caption(f"{match.players[match.chooser].name.upper()}'S TOP CARD")
            st.header(card.name, anchor=False)
            st.text(card.bio)
            st.subheader("Choose your advantage" if match.phase == "choose" else "Ledger is choosing")

            for start in (0, 2, 4):
                columns = st.columns(2)

                for i in range(start, start + 2):

                    with columns[i - start]:
                        if match.phase == "choose":
                            action_button(f"{STATS[i]} · {card.stats[i]}", "choose", f"stat_{i}", i)
                        else:
                            st.metric(STATS[i], card.stats[i], border=True)

            if match.phase == "computer":
                action_button("Let Ledger call a stat", "computer", "computer", primary=True)

    elif match.phase == "tie":
        st.header(f"Still locked: {STATS[match.locked_stat]}", anchor=False)
        st.markdown("Every player who still has cards joins this comparison. Nobody chooses a new stat.")
        if not match.piles[match.chooser]:
            st.caption(f"{match.players[match.chooser].name} has been eliminated. The locked stat carries on.")
        action_button("Reveal next cards", "tie", "tie", primary=True)

    elif match.phase == "result":
        result = match.result
        st.header(f"Round result · {STATS[result.stat]}", anchor=False)

        if result.terminal and match.draw:
            st.warning(result.message)
        elif result.tied and not result.terminal:
            st.info(result.message)
        else:
            st.success(result.message)

        columns = st.columns(len(result.played))

        for column, (seat, cid, value) in zip(columns, result.played):
            with column, st.container(border=True):
                card = match.card(cid)
                st.caption(match.players[seat].name)
                portrait(card)
                st.subheader(card.name, anchor=False)
                st.metric(STATS[result.stat], value)
        action_button("See match outcome" if result.terminal else "Continue", "continue", "continue", primary=True)

    elif match.phase == "finished":

        if match.draw:
            st.header("A thoroughly questionable draw", anchor=False)
            st.markdown("House rule: everyone ran out on the same tied round. All 36 cards remain in the pot. A rematch settles the bragging rights.")

        else:
            st.header(f"{match.players[match.winner].name} wins the guild!", anchor=False)
            st.markdown("All 36 legends are accounted for. The paperwork will be unbearable.")
        st.button("Rematch with latest deck", key="rematch", type="primary", on_click=start_match,
                  args=(match.players, serial, True))
        st.button("Back to the tavern", key="back", on_click=leave_match, args=(serial,))

    if match.phase != "finished":

        with st.expander("Leave this match"):
            st.caption("Return to the tavern and discard this deal.")
            st.button("End match & return", key="end_match", on_click=leave_match, args=(serial,))
