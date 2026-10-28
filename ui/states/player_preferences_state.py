
import pygame as pg
from .wager_behavior_state import WagerBehaviorState

from .base_state import BaseState


class PlayerPreferencesState(BaseState):
    transparent = True

    PANEL = pg.FRect(390, 150, 500, 500)

    WAGER_BEHAVIOR_BUTTON = pg.FRect(440, 255, 400, 65)
    WORKING_STATUS_BUTTON = pg.FRect(440, 345, 400, 65)
    BACK_BUTTON = pg.FRect(490, 545, 300, 60)

    def __init__(self, app, playing_state=None):
        super().__init__(app)

        self.playing = playing_state

        self.title_font = pg.font.SysFont(
            None, 40, bold=True
        )
        self.font = pg.font.SysFont(None, 28)

    def go_back(self):
        self.app.states.pop()

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.go_back()
            return

        if (
            event.type != pg.MOUSEBUTTONDOWN
            or event.button != 1
        ):
            return

        if self.WAGER_BEHAVIOR_BUTTON.collidepoint(event.pos):
            self.open_wager_behavior()

        elif self.BACK_BUTTON.collidepoint(event.pos):
            self.go_back()


    def update(self, dt):
        pass

    def draw(self, screen):
        shade = pg.Surface(
            screen.get_size(),
            pg.SRCALPHA,
        )
        shade.fill((0, 0, 0, 120))
        screen.blit(shade, (0, 0))

        pg.draw.rect(
            screen,
            (45, 45, 45),
            self.PANEL,
            border_radius=12,
        )

        pg.draw.rect(
            screen,
            (180, 180, 180),
            self.PANEL,
            width=2,
            border_radius=12,
        )

        title = self.title_font.render(
            "PLAYER PREFERENCES",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title,
            title.get_frect(
                center=(self.PANEL.centerx, 195)
            ),
        )

        # These entries will become active as
        # their configuration screens are connected.
        for rect, label, enabled in (
            (
                self.WAGER_BEHAVIOR_BUTTON,
                "WAGER BEHAVIOR",
                True,
            ),
            (
                self.WORKING_STATUS_BUTTON,
                "WORKING STATUS",
                False,
            ),
        ):
            pg.draw.rect(
                screen,
                (65, 95, 125) if enabled else (65, 65, 65),
                rect,
                border_radius=8,
            )

            text = self.font.render(
                label,
                True,
                (245, 245, 245)
                if enabled else (145, 145, 145),
            )

            screen.blit(
                text,
                text.get_frect(center=rect.center),
            )

        pg.draw.rect(
            screen,
            (75, 75, 75),
            self.BACK_BUTTON,
            border_radius=8,
        )

        back = self.font.render(
            "BACK",
            True,
            (245, 245, 245),
        )

        screen.blit(
            back,
            back.get_frect(
                center=self.BACK_BUTTON.center
            ),
        )


    def open_wager_behavior(self):
        self.app.states.push(
            WagerBehaviorState(
                self.app,
                self.playing,
            )
        )