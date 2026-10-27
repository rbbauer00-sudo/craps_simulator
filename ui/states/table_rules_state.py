
from dataclasses import replace

import pygame as pg

from engine import VigSetting

from .base_state import BaseState


class TableRulesState(BaseState):
    RULES = (
        "BUY VIG",
        "AUTO BUY LEVEL",
        "FIELD 12",
        "PUT BETS",
    )

    BACK_BUTTON = pg.FRect(490, 625, 300, 55)

    VIG_OPTIONS = (
        VigSetting.AUTO_BUY,
        VigSetting.ON_WIN,
        VigSetting.UP_FRONT,
    )

    def __init__(self, app, new_game_state):
        super().__init__(app)

        self.setup = new_game_state
        self.font = pg.font.SysFont(None, 28)
        self.title_font = pg.font.SysFont(
            None, 44, bold=True
        )

        self.left_buttons = {}
        self.right_buttons = {}

        for index, rule in enumerate(self.RULES):
            y = 235 + index * 85

            self.left_buttons[rule] = pg.FRect(
                690, y, 50, 50
            )
            self.right_buttons[rule] = pg.FRect(
                790, y, 50, 50
            )

    @property
    def settings(self):
        return self.setup.game_settings

    def change_rule(self, rule, direction):
        settings = self.settings

        if rule == "BUY VIG":
            index = self.VIG_OPTIONS.index(
                settings.buy_vig_setting
            )

            value = self.VIG_OPTIONS[
                (index + direction) % len(self.VIG_OPTIONS)
            ]

            settings = replace(
                settings,
                buy_vig_setting=value,
            )

        elif rule == "AUTO BUY LEVEL":
            settings = replace(
                settings,
                auto_buy_level=max(
                    1,
                    settings.auto_buy_level + 5 * direction,
                ),
            )

        elif rule == "FIELD 12":
            settings = replace(
                settings,
                field_3x_on_12=not settings.field_3x_on_12,
            )

        elif rule == "PUT BETS":
            settings = replace(
                settings,
                allow_put_bets=not settings.allow_put_bets,
            )

        self.setup.game_settings = settings

    def value_for(self, rule):
        settings = self.settings

        match rule:
            case "BUY VIG":
                return settings.buy_vig_setting.name.replace(
                    "_", " "
                )
            case "AUTO BUY LEVEL":
                return f"${settings.auto_buy_level}"
            case "FIELD 12":
                return (
                    "3:1" if settings.field_3x_on_12
                    else "2:1"
                )
            case "PUT BETS":
                return (
                    "YES" if settings.allow_put_bets
                    else "NO"
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

        for rule in self.RULES:
            if self.left_buttons[rule].collidepoint(event.pos):
                self.change_rule(rule, -1)
                return

            if self.right_buttons[rule].collidepoint(event.pos):
                self.change_rule(rule, 1)
                return

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((25, 40, 35))

        title = self.title_font.render(
            "TABLE RULES",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title,
            title.get_frect(center=(640, 145)),
        )

        for rule in self.RULES:
            left = self.left_buttons[rule]
            right = self.right_buttons[rule]

            label = self.font.render(
                rule,
                True,
                (235, 235, 235),
            )
            screen.blit(label, (440, left.y + 12))

            value = self.font.render(
                self.value_for(rule),
                True,
                (245, 245, 245),
            )
            screen.blit(
                value,
                value.get_frect(
                    center=(765, left.centery)
                ),
            )

            for rect, symbol in (
                (left, "-"),
                (right, "+"),
            ):
                pg.draw.rect(
                    screen,
                    (65, 95, 125),
                    rect,
                    border_radius=6,
                )

                text = self.font.render(
                    symbol,
                    True,
                    (255, 255, 255),
                )
                screen.blit(
                    text,
                    text.get_frect(center=rect.center),
                )

        pg.draw.rect(
            screen,
            (55, 105, 80),
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
