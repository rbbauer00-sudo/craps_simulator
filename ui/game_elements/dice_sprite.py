from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui import CrapsApp
    from engine import RollResult
import pygame as pg
from pygame.math import Vector2 as Vector
from pygame.constants import *
import random

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

    def roll(self, value: int) -> None:
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
        app: CrapsApp,
        clickable_sprites: pg.sprite.Group,
        visible_sprites: pg.sprite.Group,
        gap: int = 10
    ) -> None:
        super().__init__(clickable_sprites)

        self.app = app
        self.gap = gap

        self.animation_duration = 0.6
        self.animation_elapsed = 0.0
        self.face_interval = 0.06
        self.face_elapsed= 0.0

        self.is_animating = False
        self.final_values: tuple[int, int] | None = None
        self.animation_rng = random.Random()

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


    def roll(self, roll_result:RollResult) -> None:
        if self.is_animating:
            return

        self.final_values = (
            roll_result.d1,
            roll_result.d2,
        )

        
        self.animation_elapsed = 0.0
        self.face_elapsed = 0.0
        self.is_animating = True

    def update(self, dt: float) -> None:
        if not self.is_animating:
            return

        self.animation_elapsed += dt
        self.face_elapsed += dt

        if self.animation_elapsed >= self.animation_duration:
            self.finish_animaiton()
            return

        if self.face_elapsed >= self.face_interval:
            self.face_elapsed %= self.face_interval

            self.die1.roll(
                self.animation_rng.randint(1,6)
            )
            self.die2.roll(
                self.animation_rng.randint(1,6)
            )

    def finish_animation(self) -> None:
        if self.final_values is None:
            return

        d1, d2 = self.final_values

        self.die1.roll(d1)
        self.die2.roll(d2)

        self.is_animating = False
        self.final_values = None


    