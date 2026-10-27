
import pygame as pg

from .base_state import BaseState
from engine import GameSettings
from .table_rules_state import TableRulesState


class NewGameState(BaseState):
    NAME_RECT = pg.FRect(440, 285, 400, 55)
    BANKROLL_RECT = pg.FRect(440, 385, 400, 55)

    START_BUTTON = pg.FRect(650, 560, 190, 60)
    BACK_BUTTON = pg.FRect(440, 560, 190, 60)

    RULES_BUTTON = pg.FRect(440, 455, 400, 45)

    def __init__(self, app):
        super().__init__(app)

        self.name = "Player 0"
        self.bankroll_text = "1500"
        self.active_field = None
        self.game_settings = GameSettings()

        self.font = pg.font.SysFont(None, 28)
        self.title_font = pg.font.SysFont(
            None, 48, bold=True
        )
        self.error = ""

    def start_game(self):
        try:
            bankroll = int(self.bankroll_text)
        except ValueError:
            self.error = "Enter a valid bankroll."
            return

        if bankroll <= 0:
            self.error = "Bankroll must be positive."
            return

        self.app.new_game(
            name=self.name.strip() or "Player 0",
            bankroll=bankroll,
            settings=self.game_settings,
        )

    def go_back(self):
        self.app.states.pop()

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button != 1:
                return

            if self.NAME_RECT.collidepoint(event.pos):
                self.active_field = "name"

            elif self.BANKROLL_RECT.collidepoint(event.pos):
                self.active_field = "bankroll"

            elif self.RULES_BUTTON.collidepoint(event.pos):
                self.app.states.push(
                    TableRulesState(self.app, self)
                )

            elif self.START_BUTTON.collidepoint(event.pos):
                self.start_game()

            elif self.BACK_BUTTON.collidepoint(event.pos):
                self.go_back()

            else:
                self.active_field = None

        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.go_back()
                return

            if event.key == pg.K_TAB:
                self.active_field = (
                    "bankroll"
                    if self.active_field == "name"
                    else "name"
                )
                return

            if event.key == pg.K_RETURN:
                self.start_game()
                return

            if self.active_field is None:
                return

            if event.key == pg.K_BACKSPACE:
                if self.active_field == "name":
                    self.name = self.name[:-1]
                else:
                    self.bankroll_text = (
                        self.bankroll_text[:-1]
                    )
                return

            char = event.unicode

            if self.active_field == "name":
                if char.isprintable() and len(self.name) < 30:
                    self.name += char

            elif self.active_field == "bankroll":
                if char.isascii() and char.isdigit():
                    if len(self.bankroll_text) < 9:
                        self.bankroll_text += char

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((25, 40, 35))

        title = self.title_font.render(
            "NEW GAME",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title,
            title.get_frect(center=(640, 170)),
        )

        fields = (
            (
                "Player Name",
                self.NAME_RECT,
                self.name,
                "name",
            ),
            (
                "Starting Bankroll",
                self.BANKROLL_RECT,
                self.bankroll_text,
                "bankroll",
            ),
        )

        pg.draw.rect(
            screen,
            (65, 95, 125),
            self.RULES_BUTTON,
            border_radius=8,
        )

        rules_text = self.font.render(
            "TABLE RULES",
            True,
            (245, 245, 245),
        )

        screen.blit(
            rules_text,
            rules_text.get_frect(
                center=self.RULES_BUTTON.center,
            ),
        )

        for label, rect, value, field in fields:
            label_surface = self.font.render(
                label,
                True,
                (230, 230, 230),
            )
            screen.blit(
                label_surface,
                (rect.left, rect.top - 32),
            )

            pg.draw.rect(
                screen,
                (55, 55, 55),
                rect,
                border_radius=6,
            )

            pg.draw.rect(
                screen,
                (100, 180, 130)
                if self.active_field == field
                else (150, 150, 150),
                rect,
                width=2,
                border_radius=6,
            )

            text = self.font.render(
                value,
                True,
                (245, 245, 245),
            )
            screen.blit(
                text,
                (rect.left + 12, rect.centery - 12),
            )

        for rect, label in (
            (self.BACK_BUTTON, "BACK"),
            (self.START_BUTTON, "START GAME"),
        ):
            pg.draw.rect(
                screen,
                (55, 105, 80),
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

        if self.error:
            error_text = self.font.render(
                self.error,
                True,
                (230, 120, 120),
            )
            screen.blit(
                error_text,
                error_text.get_frect(
                    center=(640, 530)
                ),
            )
