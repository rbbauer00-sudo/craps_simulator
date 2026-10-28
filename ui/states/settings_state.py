
import pygame as pg

from .base_state import BaseState
from .animation_settings_state import AnimationSettingsState
from .player_preferences_state import PlayerPreferencesState


class SettingsState(BaseState):
    transparent = True

    PANEL = pg.FRect(440, 150, 400, 500)

    PLAYER_PREFERENCES_BUTTON = pg.FRect(490, 255, 300, 65)
    ANIMATION_BUTTON = pg.FRect(490, 345, 300, 65)
    BACK_BUTTON = pg.FRect(490, 545, 300, 60)

    def __init__(self, app, playing_state=None):
        super().__init__(app)

        self.playing = playing_state

        self.title_font = pg.font.SysFont(
            None, 40, bold=True
        )
        self.font = pg.font.SysFont(None, 28)

    def open_animation_settings(self):
        self.app.states.push(
            AnimationSettingsState(
                self.app,
                self.playing,
            )
        )

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

        if self.PLAYER_PREFERENCES_BUTTON.collidepoint(event.pos):
            self.open_player_preferences()

        elif self.ANIMATION_BUTTON.collidepoint(event.pos):
            self.open_animation_settings()

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
            "SETTINGS",
            True,
            (245, 245, 245),
        )
        screen.blit(
            title,
            title.get_frect(
                center=(self.PANEL.centerx, 195)
            ),
        )

        for rect, label in (
            (
                self.PLAYER_PREFERENCES_BUTTON,
                "PLAYER PREFERENCES",
            ),
            (
                self.ANIMATION_BUTTON,
                "ANIMATION",
            ),
        ):
            pg.draw.rect(
                screen,
                (65, 95, 125),
                rect,
                border_radius=8,
            )

            text = self.font.render(
                label,
                True,
                (245, 245, 245),
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

    def open_player_preferences(self):
        self.app.states.push(
            PlayerPreferencesState(
                self.app,
                self.playing,
            )
        )