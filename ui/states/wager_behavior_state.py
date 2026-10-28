
import pygame as pg

from engine import WagerType
from .base_state import BaseState


class WagerBehaviorState(BaseState):

    WAGER_TYPES = (
        (WagerType.FIELD, "Field"),
        (WagerType.HOP, "Hop"),
        (WagerType.HARDWAY, "Hardways"),
        (WagerType.ANY_SEVEN, "Any Seven"),
        (WagerType.ANY_CRAPS, "Any Craps"),
        (WagerType.YO_LEVEN, "Yo"),
        (WagerType.ACE_DEUCE, "Ace-Deuce"),
        (WagerType.DEUCE, "Deuce"),
        (WagerType.MIDNIGHT, "Midnight"),
    )

    BACK_BUTTON = pg.FRect(490, 665, 300, 55)

    def __init__(self, app, new_game_state):
        super().__init__(app)

        self.setup = new_game_state

        self.title_font = pg.font.SysFont(
            None, 44, bold=True
        )
        self.font = pg.font.SysFont(None, 27)
        self.small_font = pg.font.SysFont(None, 21)

        self.buttons = {}

        for index, (wager_type, _) in enumerate(
            self.WAGER_TYPES
        ):
            column = index // 5
            row = index % 5

            self.buttons[wager_type] = pg.FRect(
                385 + column * 270,
                235 + row * 75,
                240,
                55,
            )

    def take_down(self, wager_type):
        return self.setup.wager_preferences.take_down_on_win.get(
            wager_type,
            False,
        )

    def toggle(self, wager_type):
        preferences = (
            self.setup.wager_preferences.take_down_on_win
        )

        preferences[wager_type] = not self.take_down(
            wager_type
        )

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.app.states.pop()
            return

        if (
            event.type != pg.MOUSEBUTTONDOWN
            or event.button != 1
        ):
            return

        if self.BACK_BUTTON.collidepoint(event.pos):
            self.app.states.pop()
            return

        for wager_type, rect in self.buttons.items():
            if rect.collidepoint(event.pos):
                self.toggle(wager_type)
                return

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((25, 40, 35))

        title = self.title_font.render(
            "WAGER BEHAVIOR",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title,
            title.get_frect(center=(640, 130)),
        )

        subtitle = self.small_font.render(
            "Choose which winning wagers return to the player",
            True,
            (200, 200, 200),
        )
        screen.blit(
            subtitle,
            subtitle.get_frect(center=(640, 185)),
        )

        for wager_type, label in self.WAGER_TYPES:
            rect = self.buttons[wager_type]

            take_down = self.take_down(wager_type)

            pg.draw.rect(
                screen,
                (105, 75, 45)
                if take_down else (45, 105, 75),
                rect,
                border_radius=8,
            )

            name = self.font.render(
                label,
                True,
                (245, 245, 245),
            )

            behavior = self.small_font.render(
                "TAKE DOWN" if take_down else "STAY UP",
                True,
                (245, 245, 245),
            )

            screen.blit(
                name,
                name.get_frect(
                    center=(rect.centerx, rect.centery - 11)
                ),
            )

            screen.blit(
                behavior,
                behavior.get_frect(
                    center=(rect.centerx, rect.centery + 13)
                ),
            )

        pg.draw.rect(
            screen,
            (65, 95, 125),
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
            back.get_frect(center=self.BACK_BUTTON.center),
        )
