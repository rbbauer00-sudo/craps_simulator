import pygame as pg

from engine import WagerType


LAMMER_TYPES = frozenset({
    WagerType.PLACE_BET,
    WagerType.HARDWAY,
})


def lammer_label(wager, point: int | None) -> str | None:
    if wager.definition.wager_type not in LAMMER_TYPES:
        return None

    if point is None and wager.is_working:
        return "ON"

    if point is not None and not wager.is_working:
        return "OFF"

    return None


def draw_working_lammer(
    screen: pg.Surface,
    wager_sprite,
    point: int | None,
    font: pg.font.Font,
) -> None:
    label = lammer_label(wager_sprite.wager, point)

    if label is None:
        return

    radius = 13

    center = (
        wager_sprite.rect.right - 3,
        wager_sprite.rect.top + 3,
    )

    if label == "ON":
        fill = (245, 245, 245)
        foreground = (25, 25, 25)
    else:
        fill = (25, 25, 25)
        foreground = (245, 245, 245)

    pg.draw.circle(screen, fill, center, radius)
    pg.draw.circle(
        screen,
        foreground,
        center,
        radius,
        width=2,
    )

    text = font.render(label, True, foreground)

    screen.blit(
        text,
        text.get_frect(center=center),
    )