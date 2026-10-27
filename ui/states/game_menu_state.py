
import pygame as pg

from .base_state import BaseState


class GameMenuState(BaseState):
    transparent = True

    PANEL = pg.FRect(440, 150, 400, 500)

    RESUME_BUTTON = pg.FRect(490, 245, 300, 65)
    NEW_GAME_BUTTON = pg.FRect(490, 330, 300, 65)
    SETTINGS_BUTTON = pg.FRect(490, 415, 300, 65)
    QUIT_BUTTON = pg.FRect(490, 500, 300, 65)

    def __init__(self, app, playing_state=None):
        super().__init__(app)

        # Retain the underlying game when the menu opens.
        self.playing = playing_state

        self.title_font = pg.font.SysFont(
            None, 44, bold=True
        )
        self.button_font = pg.font.SysFont(None, 30)

    @property
    def can_start_new_game(self) -> bool:
        return (
            self.playing is not None
            and not self.playing.is_animating
        )

    def resume_game(self):
        self.app.states.pop()

    def new_game(self):
        if self.can_start_new_game:
            self.app.new_game()

    def open_settings(self):
        from .settings_state import SettingsState

        if self.playing is not None:
            self.app.states.push(
                SettingsState(self.app, self.playing)
            )

    def quit_game(self):
        self.app.running = False

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.resume_game()
            return

        if event.type != pg.MOUSEBUTTONDOWN:
            return

        if event.button != 1:
            return

        if self.RESUME_BUTTON.collidepoint(event.pos):
            self.resume_game()

        elif self.NEW_GAME_BUTTON.collidepoint(event.pos):
            self.new_game()

        elif self.SETTINGS_BUTTON.collidepoint(event.pos):
            self.open_settings()

        elif self.QUIT_BUTTON.collidepoint(event.pos):
            self.quit_game()

    def update(self, dt):
        pass

    def draw(self, screen):
        shade = pg.Surface(
            screen.get_size(),
            pg.SRCALPHA,
        )
        shade.fill((0, 0, 0, 165))
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
            "GAME PAUSED",
            True,
            (245, 245, 245),
        )
        screen.blit(
            title,
            title.get_frect(
                center=(self.PANEL.centerx, 195)
            ),
        )

        buttons = (
            (self.RESUME_BUTTON, "RESUME", True),
            (
                self.NEW_GAME_BUTTON,
                "NEW GAME",
                self.can_start_new_game,
            ),
            (self.SETTINGS_BUTTON, "SETTINGS", True),
            (self.QUIT_BUTTON, "QUIT", True),
        )

        for rect, label, enabled in buttons:
            pg.draw.rect(
                screen,
                (65, 95, 125) if enabled
                else (65, 65, 65),
                rect,
                border_radius=8,
            )

            text = self.button_font.render(
                label,
                True,
                (245, 245, 245) if enabled
                else (130, 130, 130),
            )

            screen.blit(
                text,
                text.get_frect(center=rect.center),
            )
