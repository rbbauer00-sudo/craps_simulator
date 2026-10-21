from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.craps_app import CrapsApp
import pygame as pg
from pygame.math import Vector2 as Vector
from pygame.constants import *

pg.font.init()
DIE_FONT = pg.font.SysFont(None, 38, bold=True)



class DieSprite(pg.sprite.Sprite):
    def __init__(
        self,
        size: int,
        topleft: Vector,
        groups: list[pg.sprite.Group],
    ) -> None:
        super().__init__(*groups)
        
        self.value: int = 6
        self.size = size

        self.image = pg.surface.Surface(
            size=(size,size),
            flags=SRCALPHA,
        )

        self.rect = self.image.get_rect(
            topleft=topleft,
        )

        self.render_image()

    def set_value(self, value: int) -> None:
        if not 1 <= value <= 6:
            raise ValueError(
                "Die value must be between 1 and 6."
            )

        if self.value != value:
            self.value = value
            self.render_image()

    def render_image(self):
        self.image.fill((0,0,0,0))

        # Draw a square
        pg.draw.rect(
            surface=self.image,
            color=(220,30,30),
            rect=(0, 0, self.size, self.size),
            border_radius=6,
            )

        # Render text
        text_surf = DIE_FONT.render(
            text=str(self.value), 
            antialias=True, 
            color=(225, 225, 225),
        )

        text_rect = text_surf.get_rect(
            center = (
                self.size // 2, 
                self.size // 2
            ),
        )

        self.image.blit(
            source=text_surf, 
            dest=text_rect,
        )
        

class DiceSprite(pg.sprite.Sprite):
    def __init__(
        self,
        size: int,
        topleft: Vector,
        game: CrapsApp,
        clickable_sprites: pg.sprite.Group,
        visible_sprites: pg.sprite.Group,
        gap: int = 10
    ) -> None:
        super().__init__(clickable_sprites)

        self.game = game
        self.gap = gap

        self.die1 = DieSprite(
            size=size,
            topleft=Vector(topleft),
            groups=(
                visible_sprites,
            ),
        )

        self.die2 = DieSprite(
            size=size,
            topleft=Vector(
                self.die1.rect.right + self.gap,
                self.die1.rect.top,
            ),
            groups=(
                visible_sprites,
            ),
        )

        bounds = self.die1.rect.union(
            self.die2.rect,
        )

        self.image = pg.Surface(
            size=bounds.size,
            flags=SRCALPHA,
        )

        self.rect = bounds.copy()

    def set_values(
        self, 
        d1: int,
        d2: int,
    ) -> None:
        self.die1.set_value(d1)
        self.die2.set_value(d2)

    def on_roll(self, result) -> None:
        self.set_values(result.die1, result.die2)

    