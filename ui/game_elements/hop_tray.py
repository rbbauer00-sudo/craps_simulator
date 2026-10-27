
import pygame as pg

from engine import WagerType
from engine.constants import HOP_TARGETS


class HopTray:
    RECT = pg.FRect(25, 625, 250, 155)

    TARGETS = tuple(
        sorted(
            HOP_TARGETS,
            key=lambda pair: (sum(pair), pair),
        )
    )

    def __init__(self, engine):
        self.engine = engine
        self.font = pg.font.SysFont(None, 15)
        self.title_font = pg.font.SysFont(
            None, 19, bold=True
        )

        self.positions = {
            target: (
                48 + (index % 6) * 40,
                669 + (index // 6) * 45,
            )
            for index, target in enumerate(self.TARGETS)
        }

    def position_for(
        self,
        target: tuple[int, int],
    ) -> tuple[int, int]:
        return self.positions[tuple(sorted(target))]

    def active_wagers(self):
        return [
            wager
            for wager in self.engine.wagers
            if wager.definition.wager_type
            is WagerType.HOP
        ]

    def draw(self, screen: pg.Surface) -> None:
        pg.draw.rect(
            screen,
            (42, 42, 42),
            self.RECT,
            border_radius=6,
        )

        pg.draw.rect(
            screen,
            (145, 145, 145),
            self.RECT,
            width=1,
            border_radius=6,
        )

        title = self.title_font.render(
            f"HOPS ({len(self.active_wagers())})",
            True,
            (240, 240, 240),
        )
        screen.blit(title, (35, 630))

        for target, position in self.positions.items():
            label = self.font.render(
                f"{target[0]}-{target[1]}",
                True,
                (185, 185, 185),
            )

            screen.blit(
                label,
                label.get_frect(
                    center=(position[0], position[1] - 23)
                ),
            )
