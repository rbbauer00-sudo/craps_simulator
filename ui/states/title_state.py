
import pygame as pg

from .base_state import BaseState
from .new_game_state import NewGameState


class TitleState(BaseState):
    TITLE_POSITION = (640, 190)

    NEW_GAME_BUTTON = pg.FRect(440, 320, 400, 70)
    SETTINGS_BUTTON = pg.FRect(440, 420, 400, 70)
    QUIT_BUTTON = pg.FRect(440, 520, 400, 70)

    def __init__(self, app):
        super().__init__(app)

        self.title_font = pg.font.SysFont(
            None, 72, bold=True
        )
        self.button_font = pg.font.SysFont(
            None, 32
        )

    def start_game(self):
        self.app.states.push(
            NewGameState(self.app)
        )

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.start_game()
            return

        if event.type != pg.MOUSEBUTTONDOWN:
            return

        if event.button != 1:
            return

        if self.NEW_GAME_BUTTON.collidepoint(event.pos):
            self.start_game()

        elif self.QUIT_BUTTON.collidepoint(event.pos):
            self.app.running = False

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((25, 40, 35))

        title = self.title_font.render(
            "CRAPS SIMULATOR",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title,
            title.get_frect(
                center=self.TITLE_POSITION
            ),
        )

        buttons = (
            (self.NEW_GAME_BUTTON, "NEW GAME", True),
            (self.SETTINGS_BUTTON, "SETTINGS", False),
            (self.QUIT_BUTTON, "QUIT", True),
        )

        for rect, label, enabled in buttons:
            pg.draw.rect(
                screen,
                (45, 105, 75)
                if enabled else (55, 55, 55),
                rect,
                border_radius=10,
            )

            pg.draw.rect(
                screen,
                (150, 150, 150),
                rect,
                width=2,
                border_radius=10,
            )

            text = self.button_font.render(
                label,
                True,
                (245, 245, 245)
                if enabled else (125, 125, 125),
            )

            screen.blit(
                text,
                text.get_frect(center=rect.center),
            )
