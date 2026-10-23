
import pygame as pg
from pygame.math import Vector2 as Vector


class ChipSprite(pg.sprite.Sprite):
    def __init__(
        self,
        value: int,
        center: tuple[float, float],
        *groups: pg.sprite.AbstractGroup,
        radius: int = 25,
    ) -> None:
        super().__init__(*groups)

        self.value = value
        self.radius = radius

        diameter = radius * 2
        self.image = pg.Surface(
            (diameter, diameter),
            pg.SRCALPHA,
        )
        self.rect = self.image.get_frect(center=center)

        self.font = pg.font.SysFont(None, 24, bold=True)

        self.start_position = Vector(self.rect.center)
        self.target_position = self.start_position.copy()

        self.animation_duration = 0.0
        self.animation_elapsed = 0.0
        self.hold_duration = 0.0
        self.hold_elapsed = 0.0

        self.is_moving = False
        self.is_holding = False

        self.render_image()

    @property
    def is_animating(self) -> bool:
        return self.is_moving or self.is_holding

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
            f"${self.value}",
            True,
            (255, 255, 255),
        )

        self.image.blit(
            text,
            text.get_frect(center=center),
        )

    def move_to(
        self,
        position: tuple[float, float],
        duration: float = 0.4,
        hold: float = 0.0,
    ) -> None:
        if duration <= 0:
            raise ValueError(
                "Movement duration must be positive."
            )

        if hold < 0:
            raise ValueError(
                "Hold duration cannot be negative."
            )

        if self.is_animating:
            raise RuntimeError(
                "Chip animation already in progress."
            )

        self.start_position = Vector(self.rect.center)
        self.target_position = Vector(position)

        self.animation_duration = duration
        self.animation_elapsed = 0.0

        self.hold_duration = hold
        self.hold_elapsed = 0.0

        self.is_moving = True
        self.is_holding = False

    def hold(self, duration: float) -> None:
        if duration < 0:
            raise ValueError(
                "Hold duration cannot be negative."
            )

        if self.is_animating:
            raise RuntimeError(
                "Chip animation already in progress."
            )

        self.hold_duration = duration
        self.hold_elapsed = 0.0
        self.is_holding = duration > 0

    def update(self, dt: float) -> None:
        if self.is_moving:
            self.animation_elapsed += dt

            progress = min(
                self.animation_elapsed
                / self.animation_duration,
                1.0,
            )

            position = self.start_position.lerp(
                self.target_position,
                progress,
            )

            self.rect.center = position

            if progress >= 1.0:
                self.is_moving = False

                self.is_holding = self.hold_duration > 0
                self.hold_elapsed = 0.0

        elif self.is_holding:
            self.hold_elapsed += dt

            if self.hold_elapsed >= self.hold_duration:
                self.is_holding = False
