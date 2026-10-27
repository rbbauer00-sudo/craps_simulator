
import pygame as pg


def click(state, position, button=1):
    event = pg.event.Event(
        pg.MOUSEBUTTONDOWN,
        {
            "pos": position,
            "button": button,
        },
    )
    state.handle_event(event)


def select_chip(state, value):
    click(
        state,
        state.chip_buttons[value].center,
    )


def run_until_idle(state, max_frames=1000):
    dt = 1 / 60

    for _ in range(max_frames):
        if not state.is_animating:
            return

        state.update(dt)

    raise AssertionError(
        "UI did not return to idle state."
    )

def force_roll(state, total):
    for char in str(total):
        state.forced_roll_buffer.add(char)

    state.roll()
    run_until_idle(state)

    assert state.current_roll is None
    assert not state.is_animating