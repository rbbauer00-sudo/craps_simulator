
import pygame as pg

from .base_state import BaseState


class GameMenuState(BaseState):
    transparent = True

    PANEL = pg.FRect(440, 200, 400, 340)
    RESUME_BUTTON = pg.FRect(490, 310, 300, 65)
    QUIT_BUTTON = pg.FRect(490, 405, 300, 65)

    def __init__(self, app):
        super().__init__(app)

        self.title_font = pg.font.SysFont(
            None, 44, bold=True
        )
        self.button_font = pg.font.SysFont(None, 30)

    def resume_game(self):
        self.app.states.pop()

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

        elif self.QUIT_BUTTON.collidepoint(event.pos):
            self.quit_game()

    def update(self, dt):
        # Intentionally do nothing.
        # PlayingState is frozen beneath this overlay.
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
                center=(self.PANEL.centerx, 255)
            ),
        )

        for rect, label in (
            (self.RESUME_BUTTON, "RESUME"),
            (self.QUIT_BUTTON, "QUIT"),
        ):
            pg.draw.rect(
                screen,
                (65, 95, 125),
                rect,
                border_radius=8,
            )

            text = self.button_font.render(
                label,
                True,
                (245, 245, 245),
            )

            screen.blit(
                text,
                text.get_frect(center=rect.center),
            )
