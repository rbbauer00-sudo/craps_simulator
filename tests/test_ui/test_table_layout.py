
from itertools import combinations

import pygame as pg

from ui.layout.table_layout import TableLayout


def test_betting_areas_do_not_overlap():
    areas = TableLayout.create_betting_areas()

    for a, b in combinations(areas, 2):
        assert not a.rect.colliderect(b.rect), (
            f"{a.name} overlaps {b.name}"
        )


def test_betting_area_names_unique():
    areas = TableLayout.create_betting_areas()
    names = [area.name for area in areas]

    assert len(names) == len(set(names))


def test_all_areas_inside_table_or_sidebar():
    layout = TableLayout()

    for area in layout.create_betting_areas():
        assert (
            layout.TABLE_RECT.contains(area.rect)
            or layout.SIDEBAR_RECT.contains(area.rect)
        ), area.name


def test_traveled_wagers_clear_of_betting_areas():
    layout = TableLayout()
    areas = layout.create_betting_areas()

    positions = (
        list(layout.COME_POSITIONS.values())
        + list(layout.DONT_COME_POSITIONS.values())
    )

    for position in positions:
        rect = pg.FRect(0, 0, 50, 50)
        rect.center = position

        for area in areas:
            assert not rect.colliderect(area.rect), (
                f"Travel position {position} overlaps "
                f"{area.name}"
            )


def test_dice_clear_of_betting_areas(ui_app):
    state = ui_app.states.current

    # Use the actual sprite bounds.
    dice_rect = state.dice_sprite.rect

    for area in state.areas:
        assert not dice_rect.colliderect(area.rect), (
            f"Dice overlap {area.name}"
        )


def test_bonus_panel_clear_of_betting_areas(ui_app):
    state = ui_app.states.current
    panel = state.bonus_progress_sprite.rect

    for area in state.areas:
        assert not panel.colliderect(area.rect), (
            f"Bonus panel overlaps {area.name}"
        )


def test_hop_tray_clear_of_controls():
    from ui.game_elements.hop_tray import HopTray

    layout = TableLayout()

    for rect in (
        *layout.CHIP_BUTTONS.values(),
        *layout.TOOL_BUTTONS.values(),
    ):
        assert not HopTray.RECT.colliderect(rect)
