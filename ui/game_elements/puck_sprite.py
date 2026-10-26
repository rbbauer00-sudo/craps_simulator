import pygame as pg
from pygame.math import Vector2 as Vector

class PuckSprite(pg.sprite.Sprite):
    POINT_POSITIONS = {
        4: (170, 110),
        5: (280, 110),
        6: (390, 110),
        8: (500, 110),
        9: (610, 110),
        10: (720, 110),
        None: (850, 110),

    }
                    
    def __init__(
        self,
        point: int | None = None,
        *groups: pg.sprite.AbstractGroup,
    ) -> None:
        super().__init__(*groups)

        self.point = point
        self.target_point: int | None = point
        self.radius = 24

        diameter = self.radius * 2

        self.image = pg.Surface(
            (diameter, diameter),
            pg.SRCALPHA,
        )

        self.rect = self.image.get_frect(
            center=self.position_for(point),
        )

        self.start_position = Vector(self.rect.center)
        self.target_position = self.start_position.copy()

        self.animation_duration = 0.4
        self.animation_elapsed = 0.0
        self.is_animating = False

        self.font = pg.font.SysFont(None, 25, bold=True)

        self.render_image()


    def position_for(
        self,
        point: int | None,
    ) -> tuple[int, int]:
        
        return self.POINT_POSITIONS[point]
    

    def render_image(self) -> None:
        self.image.fill((0,0,0,0))

        black = (30,30,30)
        white = (245,245,245)

        pg.draw.circle(
            self.image,
            white if self.point else black,
            (self.radius, self.radius),
            self.radius,
        )
        
        pg.draw.circle(
            self.image,
            black if self.point else white,
            (self.radius, self.radius),
            self.radius,
            width=2
        )

        text = self.font.render(
            f"{self.point}" if self.point else "OFF",
            True,
            black if self.point else white
        )

        self.image.blit(
            text,
            text.get_frect(
                center=(self.radius, self.radius,),
            ),
        )


    def on_roll(
        self,
        point_before: int | None,
        point_after: int | None,
    ) -> None:
        if self.is_animating:
            raise RuntimeError(
                "Puck animation already in progress."
            )

        if point_before != self.point:
            raise ValueError(
                "Puck state is out of sync with engine."
            )

        if point_before == point_after:
            return

        self.target_point = point_after
        self.render_image()

        self.start_position = Vector(self.rect.center)
        self.target_position = Vector(
            self.position_for(point_after)
        )

        self.animation_elapsed = 0.0
        self.is_animating = True


    def update(self, dt: float) -> None:
        if not self.is_animating:
            return

        self.animation_elapsed += dt

        progress = min(
            self.animation_elapsed / self.animation_duration,
            1.0,
        )

        position = self.start_position.lerp(
            self.target_position,
            progress,
        )

        self.rect.center = (
            position.x,
            position.y,
        )

        if progress >= 1.0:
            self.is_animating = False
