
from __future__ import annotations
from typing import TYPE_CHECKING
from .chip_sprite import ChipSprite

import pygame as pg

if TYPE_CHECKING:
    from engine import Wager


class WagerSprite(ChipSprite):
    def __init__(
        self,
        wager: Wager,
        center: tuple[int, int],
        *groups: pg.sprite.AbstractGroup,
    ) -> None:
        self.wager = wager

        super().__init__(
            wager.value,
            center,
            *groups,
        )

        self.displayed_working = self.wager.is_working
        self.render_image()


    def render_image(self) -> None:
        self.value = self.wager.value

        super().render_image()

        if not self.wager.is_working:
            center = (self.radius, self.radius)

            self.image.fill((0,0,0,0))

            pg.draw.circle(
                self.image,
                (85,85,85),
                center,
                self.radius,
            )

            pg.draw.circle(
                self.image,
                (235,235,235),
                center,
                self.radius,
                width=3,
            )

            text = self.font.render(
                f"${self.value}",
                True,
                (255,255,255),
            )

            self.image.blit(
                text,
                text.get_frect(center=center),
            )

        self.displayed_working = self.wager.is_working


    def update(self, dt: float):
        super().update(dt)

        if (
            self.wager.value != self.value
            or self.wager.is_working != self.displayed_working
        ):
            self.render_image()
