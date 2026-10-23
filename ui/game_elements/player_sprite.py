from __future__ import annotations
from typing import TYPE_CHECKING

import pygame as pg

if TYPE_CHECKING:
    from engine import Player

class PlayerSprite(pg.sprite.Sprite):
    def __init__(
        self,
        player: Player,
        topleft: tuple[int, int],
        *groups: pg.sprite.AbstractGroup,
    ) -> None:
        super().__init__(*groups)

        self.player = player

        self.image = pg.Surface(
            (240, 75),
            pg.SRCALPHA,
        )

        self.rect = self.image.get_frect(
            topleft=topleft,
        )

        self.name_font = pg.font.SysFont(
            None, 24, bold=True,
        )
        self.value_font = pg.font.SysFont(
            None, 28,
        )

        self.displayed_bankroll: int | None = player.bankroll
        self.auto_sync = True

        self.render_image()


    def render_image(self) -> None:
        self.image.fill((0,0,0,0))

        pg.draw.rect(
            self.image,
            (45, 45, 45),
            self.image.get_frect(),
            border_radius=8,
        )

        pg.draw.rect(
            self.image,
            (160, 160, 160),
            self.image.get_frect(),
            width=2,
            border_radius=8
        )

        name = self.name_font.render(
            self.player.name,
            True,
            (235, 235, 235),
        )

        bankroll = self.value_font.render(
            f"Bankroll: ${self.displayed_bankroll:,}",
            True,
            (255, 255, 255),
        )

        self.image.blit(name, (12,10))
        self.image.blit(bankroll, (12, 38))


    def sync_bankroll(self) -> None:
        if self.displayed_bankroll != self.player.bankroll:
            self.displayed_bankroll = self.player.bankroll
            self.render_image()

    def update(self, dt: float) -> None:
        if self.auto_sync:
            self.sync_bankroll()