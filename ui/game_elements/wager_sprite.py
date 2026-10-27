
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
        radius: int = 25
    ) -> None:
        self.wager = wager

        super().__init__(
            wager.value,
            center,
            *groups,
            radius=radius,
        )

        self.displayed_working = self.wager.is_working
        self.displayed_buy = self.wager.is_buy
        self.render_image()
        self.auto_sync_value = True


    def render_image(self) -> None:
        self.value = self.wager.value

        if not self.wager.is_working:
            self.color = (85, 85, 85)
        elif self.wager.is_buy:
            self.color = (160, 105, 35)
        else:
            self.color = (35, 74, 180)

        super().render_image()

        self.displayed_working = self.wager.is_working
        self.displayed_buy = self.wager.is_buy


    def update(self, dt: float):
        super().update(dt)

        value_changed = (
            self.auto_sync_value
            and self.wager.value != self.value
        )

        working_changed = (
            self.wager.is_working != self.displayed_working
        )

        buy_changed = (
            self.wager.is_buy != self.displayed_buy
        )

        if (
            value_changed 
            or working_changed
            or buy_changed
        ):
            self.render_image()

        


    def sync_value(self) -> None:
        if self.value != self.wager.value:
            self.value = self.wager.value
            self.render_image()