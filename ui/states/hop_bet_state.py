
import pygame as pg

from engine import (
    WagerType,
    GameRuleViolation,
    InsufficientFundsError,
    defs,
)
from engine.constants import HOP_TARGETS

from .base_state import BaseState


class HopBetState(BaseState):
    transparent = True

    PANEL = pg.FRect(250, 70, 780, 530)
    CLOSE = pg.FRect(980, 85, 35, 35)

    TARGETS = tuple(
        sorted(
            HOP_TARGETS,
            key=lambda pair: (sum(pair), pair),
        )
    )

    def __init__(self, app, playing_state):
        super().__init__(app)
        self.playing = playing_state

        self.buttons = {
            target: pg.FRect(
                275 + (index % 5) * 150,
                185 + (index // 5) * 85,
                135,
                70,
            )
            for index, target in enumerate(self.TARGETS)
        }

    def close(self):
        self.app.states.pop()

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.close()
            return

        if event.type != pg.MOUSEBUTTONDOWN:
            return

        if event.button not in (1, 3):
            return

        position = event.pos

        # Pass chip selection through to PlayingState.
        if event.button == 1:
            if self.playing.handle_chip_click(position):
                return

        # Don't allow edits while a chip is moving.
        if self.playing.is_animating:
            return

        if event.button == 1 and self.CLOSE.collidepoint(position):
            self.close()
            return

        for target, rect in self.buttons.items():
            if rect.collidepoint(position):
                self.change_hop(target, event.button)
                return

        # Clicking outside the panel closes it, except
        # for the chip selector handled above.
        if not self.PANEL.collidepoint(position):
            self.close()

    def change_hop(self, target, button):
        existing = self.playing.engine.get_wager(
            self.playing.player,
            WagerType.HOP,
            target=target,
        )

        amount = self.playing.selected_chip
        if button == 3:
            amount = -amount

        try:
            self.playing.change_wager(
                amount,
                wager=existing,
                definition=defs.HOP_BET,
                target=target,
                position=self.playing.hop_tray.position_for(
                    target
                ),
            )
        except (
            GameRuleViolation,
            InsufficientFundsError,
        ) as exc:
            print(f"Cannot change Hop wager: {exc}")

    def update(self, dt):
        # Continue placement/removal animations underneath
        # the popup, without accepting normal table input.
        self.playing.update(dt)

    def draw(self, screen):
        # Dim only the upper part of the window.
        # The bottom chip selector remains unobscured.
        shade = pg.Surface((1280, 610), pg.SRCALPHA)
        shade.fill((0, 0, 0, 135))
        screen.blit(shade, (0, 0))

        pg.draw.rect(
            screen,
            (48, 48, 48),
            self.PANEL,
            border_radius=10,
        )

        pg.draw.rect(
            screen,
            (195, 195, 195),
            self.PANEL,
            width=2,
            border_radius=10,
        )

        title = self.app.font.render(
            "HOP BETS",
            True,
            (245, 245, 245),
        )
        screen.blit(title, (275, 95))

        selected = self.app.small_font.render(
            f"Selected chip: ${self.playing.selected_chip}"
            "     Left click: add    Right click: subtract",
            True,
            (220, 220, 220),
        )
        screen.blit(selected, (275, 145))

        pg.draw.rect(
            screen,
            (105, 45, 45),
            self.CLOSE,
            border_radius=5,
        )

        close_label = self.app.font.render(
            "X", True, (255, 255, 255)
        )
        screen.blit(
            close_label,
            close_label.get_frect(center=self.CLOSE.center),
        )

        for target, rect in self.buttons.items():
            wager = self.playing.engine.get_wager(
                self.playing.player,
                WagerType.HOP,
                target=target,
            )

            active = wager is not None
            hard = target[0] == target[1]
            payout = 30 if hard else 15

            pg.draw.rect(
                screen,
                (45, 105, 75) if active else (72, 72, 72),
                rect,
                border_radius=6,
            )

            pg.draw.rect(
                screen,
                (180, 180, 180),
                rect,
                width=1,
                border_radius=6,
            )

            name = self.app.font.render(
                f"{target[0]}-{target[1]}",
                True,
                (245, 245, 245),
            )

            details = self.app.small_font.render(
                (
                    f"${wager.value}  |  {payout}:1"
                    if active
                    else f"{payout}:1"
                ),
                True,
                (230, 230, 230),
            )

            screen.blit(
                name,
                name.get_frect(
                    center=(rect.centerx, rect.centery - 11)
                ),
            )

            screen.blit(
                details,
                details.get_frect(
                    center=(rect.centerx, rect.centery + 17)
                ),
            )
