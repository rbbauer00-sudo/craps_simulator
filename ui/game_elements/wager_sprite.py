
from __future__ import annotations
from typing import TYPE_CHECKING

import pygame as pg

if TYPE_CHECKING:
    from engine import Wager


class WagerSprite(pg.sprite.Sprite):
    def __init__(
        self,
        wager: Wager,
        center: tuple[int, int],
        *groups: pg.sprite.AbstractGroup,
    ) -> None:
        super().__init__(*groups)

        self.wager = wager
        self.radius = 25

        self.image = pg.Surface(
            (self.radius * 2, self.radius * 2),
            pg.SRCALPHA,
        )

        self.rect = self.image.get_frect(
            center=center,
        )

        self.font = pg.font.SysFont(
            None, 24, bold=True
        )

        self.render_image()

    def render_image(self) -> None:
        self.image.fill((0, 0, 0, 0))

        center = (self.radius, self.radius)

        pg.draw.circle(
            self.image,
            (35, 75, 180),
            center,
            self.radius,
        )

        pg.draw.circle(
            self.image,
            (235, 235, 235),
            center,
            self.radius,
            width=3,
        )

        text = self.font.render(
            f"${self.wager.value}",
            True,
            (255, 255, 255),
        )

        self.image.blit(
            text,
            text.get_rect(center=center),
        )
