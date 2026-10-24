
import pygame as pg

from .wager_sprite import WagerSprite


class VigSprite(pg.sprite.Sprite):
    def __init__(
        self,
        parent: WagerSprite,
    ) -> None:
        super().__init__()

        self.parent = parent
        self.value = parent.wager.collected_vig
        self.radius = 14

        diameter = self.radius * 2

        self.image = pg.Surface(
            (diameter, diameter),
            pg.SRCALPHA,
        )

        self.rect = self.image.get_frect()

        self.font = pg.font.SysFont(
            None, 16, bold=True,
        )

        self.render_image()
        self.follow_parent()

    def follow_parent(self) -> None:
        x, y = self.parent.rect.center

        self.rect.center = (
            x + 32,
            y + 22,
        )

    def render_image(self) -> None:
        self.image.fill((0, 0, 0, 0))

        center = (self.radius, self.radius)

        pg.draw.circle(
            self.image,
            (180, 130, 45),
            center,
            self.radius,
        )

        pg.draw.circle(
            self.image,
            (245, 245, 245),
            center,
            self.radius,
            width=2,
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

    def update(self, dt: float) -> None:
        self.follow_parent()

        value = self.parent.wager.collected_vig

        if value != self.value:
            self.value = value
            self.render_image()
