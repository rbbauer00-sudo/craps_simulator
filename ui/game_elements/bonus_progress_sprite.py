
import pygame as pg

from engine import WagerType


class BonusProgressSprite(pg.sprite.Sprite):
    ATS_NUMBERS = (2, 3, 4, 5, 6, 8, 9, 10, 11, 12)
    FIRE_NUMBERS = (4, 5, 6, 8, 9, 10)

    ATS_TYPES = {
        WagerType.ATS_SMALL,
        WagerType.ATS_TALL,
        WagerType.ATS_ALL,
    }

    def __init__(
        self,
        engine,
        topleft: tuple[int, int],
        *groups: pg.sprite.AbstractGroup,
    ) -> None:
        super().__init__(*groups)

        self.engine = engine

        self.image = pg.Surface((160, 175), pg.SRCALPHA)
        self.rect = self.image.get_frect(topleft=topleft)

        self.font = pg.font.SysFont(None, 19)
        self.small_font = pg.font.SysFont(None, 16)

        self._displayed_state = None
        self.update(0)


    def progress(self):
        ats_wagers = [
            wager for wager in self.engine.wagers
            if wager.definition.wager_type in self.ATS_TYPES
        ]

        fire_wager = next(
            (
                wager for wager in self.engine.wagers
                if wager.definition.wager_type
                is WagerType.FIRE_BET
            ),
            None,
        )

        ats_hits = frozenset().union(
            *(wager.targets_hit for wager in ats_wagers)
        )

        fire_hits = (
            frozenset(fire_wager.targets_hit)
            if fire_wager is not None
            else frozenset()
        )

        active_ats = frozenset(
            wager.definition.wager_type
            for wager in ats_wagers
        )

        return (
            frozenset(ats_hits),
            frozenset(fire_hits),
            active_ats,
            fire_wager is not None,
        )


    def update(self, dt: float) -> None:
        state = self.progress()

        if state != self._displayed_state:
            self._displayed_state = state
            self.render_image()


    def draw_numbers(
        self,
        numbers: tuple[int, ...],
        hits: frozenset[int],
        y: int,
        active: bool,
        color: tuple[int, int, int],
    ) -> None:
        for index, number in enumerate(numbers):
            column = index % 5
            row = index // 5

            rect = pg.FRect(
                7 + column * 30,
                y + row * 27,
                26,
                23,
            )

            fill = (
                color
                if active and number in hits
                else (65, 65, 65)
            )

            pg.draw.rect(
                self.image,
                fill,
                rect,
                border_radius=4,
            )

            text = self.font.render(
                str(number),
                True,
                (240, 240, 240),
            )

            self.image.blit(
                text,
                text.get_frect(center=rect.center),
            )


    def render_image(self) -> None:
        ats_hits, fire_hits, active_ats, fire_active = (
            self._displayed_state
        )

        self.image.fill((0, 0, 0, 0))

        pg.draw.rect(
            self.image,
            (40, 40, 40),
            self.image.get_frect(),
            border_radius=8,
        )

        pg.draw.rect(
            self.image,
            (130, 130, 130),
            self.image.get_frect(),
            width=2,
            border_radius=8,
        )

        ats_label = self.font.render(
            "ATS",
            True,
            (235, 235, 235),
        )
        self.image.blit(ats_label, (8, 6))

        labels = (
            (WagerType.ATS_SMALL, "S"),
            (WagerType.ATS_TALL, "T"),
            (WagerType.ATS_ALL, "A"),
        )

        for index, (wager_type, label) in enumerate(labels):
            text = self.small_font.render(
                label,
                True,
                (100, 220, 150)
                if wager_type in active_ats
                else (120, 120, 120),
            )
            self.image.blit(text, (90 + index * 20, 8))

        self.draw_numbers(
            self.ATS_NUMBERS,
            ats_hits,
            y=30,
            active=bool(active_ats),
            color=(30, 125, 75),
        )

        fire_label = self.font.render(
            "FIRE",
            True,
            (235, 235, 235),
        )
        self.image.blit(fire_label, (8, 94))

        count = self.small_font.render(
            f"{len(fire_hits)}/6" if fire_active else "-/6",
            True,
            (235, 235, 235),
        )
        self.image.blit(count, (125, 97))

        self.draw_numbers(
            self.FIRE_NUMBERS,
            fire_hits,
            y=120,
            active=fire_active,
            color=(165, 80, 35),
        )
