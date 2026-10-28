
import pygame as pg

from .base_state import BaseState
from engine import GameSettings
from .table_rules_state import TableRulesState
from ui.settings import WagerPreferences
from .wager_behavior_state import WagerBehaviorState


class NewGameState(BaseState):
    NAME_RECT = pg.FRect(440, 285, 400, 55)
    BANKROLL_RECT = pg.FRect(440, 385, 400, 55)

    START_BUTTON = pg.FRect(650, 605, 190, 60)
    BACK_BUTTON = pg.FRect(440, 605, 190, 60)

    RULES_BUTTON = pg.FRect(440, 455, 400, 45)
    BEHAVIOR_BUTTON = pg.FRect(440, 505, 400, 45)


    def __init__(self, app):
        super().__init__(app)

        self.name = "Player 0"
        self.bankroll_text = "1500"
        self.active_field = "name"
        self.text_selected = True
        self.caret_elapsed = 0.0
        self.game_settings = app.engine.settings

        self.wager_preferences = WagerPreferences(
            take_down_on_win=dict(
                app.wager_preferences.take_down_on_win
            )
        )

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
            wager_preferences=self.wager_preferences,
        )

    def go_back(self):
        self.app.states.pop()

    
    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button != 1:
                return

            if self.NAME_RECT.collidepoint(event.pos):
                self.focus_field("name")

            elif self.BANKROLL_RECT.collidepoint(event.pos):
                self.focus_field("bankroll")

            elif self.RULES_BUTTON.collidepoint(event.pos):
                self.app.states.push(
                    TableRulesState(self.app, self)
                )

            elif self.BEHAVIOR_BUTTON.collidepoint(event.pos):
                self.app.states.push(
                    WagerBehaviorState(self.app, self)
                )

            elif self.START_BUTTON.collidepoint(event.pos):
                self.start_game()

            elif self.BACK_BUTTON.collidepoint(event.pos):
                self.go_back()

            else:
                self.active_field = None
                self.text_selected = False

            return

        if event.type != pg.KEYDOWN:
            return

        if event.key == pg.K_ESCAPE:
            self.go_back()
            return

        if event.key == pg.K_RETURN:
            self.start_game()
            return

        if event.key == pg.K_TAB:
            next_field = (
                "bankroll"
                if self.active_field == "name"
                else "name"
            )
            self.focus_field(next_field)
            return

        if self.active_field is None:
            return

        # Ctrl+A on Windows/Linux, Cmd+A on macOS.
        if (
            event.key == pg.K_a
            and event.mod & (pg.KMOD_CTRL | pg.KMOD_META)
        ):
            self.text_selected = True
            return

        current = self.field_value(self.active_field)

        if event.key == pg.K_BACKSPACE:
            value = (
                ""
                if self.text_selected
                else current[:-1]
            )

            self.set_field_value(self.active_field, value)
            self.text_selected = False
            self.caret_elapsed = 0.0
            return

        # Ignore keyboard shortcuts other than Select All.
        if event.mod & (pg.KMOD_CTRL | pg.KMOD_META | pg.KMOD_ALT):
            return

        char = event.unicode

        if not char or not char.isprintable():
            return

        if self.active_field == "bankroll":
            if not (char.isascii() and char.isdigit()):
                return
            limit = 9
        else:
            limit = 30

        value = (
            ""
            if self.text_selected
            else current
        )

        if len(value) >= limit:
            return

        self.set_field_value(
            self.active_field,
            value + char,
        )

        self.text_selected = False
        self.caret_elapsed = 0.0
        self.error = ""


    def update(self, dt):
        self.caret_elapsed = (
            self.caret_elapsed + dt
        ) % 1.0


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
            focused = self.active_field == field
            selected = focused and self.text_selected

            label_surface = self.font.render(
                label,
                True,
                (230, 230, 230),
            )

            screen.blit(
                label_surface,
                (rect.left, rect.top - 32),
            )

            # Brighter background for the active field.
            pg.draw.rect(
                screen,
                (55, 70, 65) if focused else (55, 55, 55),
                rect,
                border_radius=6,
            )

            pg.draw.rect(
                screen,
                (100, 220, 150)
                if focused else (150, 150, 150),
                rect,
                width=3 if focused else 2,
                border_radius=6,
            )

            text_pos = (
                rect.left + 12,
                rect.centery - self.font.get_height() / 2,
            )

            text_surface = self.font.render(
                value,
                True,
                (245, 245, 245),
            )

            # Highlight selected text.
            if selected and value:
                highlight_rect = pg.FRect(
                    text_pos[0] - 2,
                    rect.centery - 16,
                    self.font.size(value)[0] + 4,
                    32,
                )

                pg.draw.rect(
                    screen,
                    (50, 105, 160),
                    highlight_rect,
                    border_radius=3,
                )

            screen.blit(text_surface, text_pos)

            # Blinking caret when text isn't selected.
            if (
                focused
                and not selected
                and self.caret_elapsed < 0.5
            ):
                caret_x = (
                    text_pos[0]
                    + self.font.size(value)[0]
                    + 2
                )

                pg.draw.line(
                    screen,
                    (245, 245, 245),
                    (caret_x, rect.centery - 14),
                    (caret_x, rect.centery + 14),
                    width=2,
                )

        pg.draw.rect(
            screen,
            (65, 95, 125),
            self.BEHAVIOR_BUTTON,
            border_radius=8,
        )

        behavior_text = self.font.render(
            "WAGER BEHAVIOR",
            True,
            (245, 245, 245),
        )

        screen.blit(
            behavior_text,
            behavior_text.get_frect(
                center=self.BEHAVIOR_BUTTON.center,
            ),
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
                    center=(640, 575)
                ),
            )

    def focus_field(self, field: str) -> None:
        self.active_field = field
        self.text_selected = True
        self.caret_elapsed = 0.0


    def field_value(self, field: str) -> str:
        if field == "name":
            return self.name
        if field == "bankroll":
            return self.bankroll_text
        raise ValueError(f"Unknown field: {field}")


    def set_field_value(self, field: str, value: str) -> None:
        if field == "name":
            self.name = value
        elif field == "bankroll":
            self.bankroll_text = value
        else:
            raise ValueError(f"Unknown field: {field}")