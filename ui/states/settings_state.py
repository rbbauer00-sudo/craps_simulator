
import pygame as pg

from ui.animations import (
    AnimationMode,
    AnimationSettings,
)

from .base_state import BaseState


class SettingsState(BaseState):
    transparent = True

    PANEL = pg.FRect(440, 150, 400, 500)
    BACK_BUTTON = pg.FRect(490, 545, 300, 60)

    MODES = tuple(AnimationMode)

    def __init__(self, app, playing_state):
        super().__init__(app)

        self.playing = playing_state

        self.mode_buttons = {
            mode: pg.FRect(
                490,
                245 + index * 70,
                300,
                55,
            )
            for index, mode in enumerate(self.MODES)
        }

        self.title_font = pg.font.SysFont(
            None, 38, bold=True
        )
        self.font = pg.font.SysFont(None, 27)
        self.small_font = pg.font.SysFont(None, 19)

    @property
    def can_change_animation(self) -> bool:
        return not self.playing.is_animating

    def select_mode(self, mode: AnimationMode):
        if not self.can_change_animation:
            return

        self.app.set_animation_settings(
            AnimationSettings(
                mode=mode,
                speed=self.app.animation_settings.speed,
            ),
            playing_state=self.playing,
        )

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.app.states.pop()
            return

        if event.type != pg.MOUSEBUTTONDOWN:
            return

        if event.button != 1:
            return

        if self.BACK_BUTTON.collidepoint(event.pos):
            self.app.states.pop()
            return

        for mode, rect in self.mode_buttons.items():
            if rect.collidepoint(event.pos):
                self.select_mode(mode)
                return

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
            "ANIMATION SETTINGS",
            True,
            (245, 245, 245),
        )
        screen.blit(
            title,
            title.get_frect(
                center=(self.PANEL.centerx, 195)
            ),
        )

        for mode, rect in self.mode_buttons.items():
            selected = (
                self.app.animation_settings.mode is mode
            )

            enabled = self.can_change_animation

            color = (
                (55, 115, 80) if selected
                else (65, 95, 125)
            ) if enabled else (65, 65, 65)

            pg.draw.rect(
                screen,
                color,
                rect,
                border_radius=8,
            )

            label = self.font.render(
                mode.name,
                True,
                (245, 245, 245) if enabled
                else (145, 145, 145),
            )

            screen.blit(
                label,
                label.get_frect(center=rect.center),
            )

        if not self.can_change_animation:
            message = self.small_font.render(
                "Finish the current animation to change modes",
                True,
                (220, 180, 120),
            )
            screen.blit(
                message,
                message.get_frect(
                    center=(self.PANEL.centerx, 525)
                ),
            )

        pg.draw.rect(
            screen,
            (75, 75, 75),
            self.BACK_BUTTON,
            border_radius=8,
        )

        label = self.font.render(
            "BACK",
            True,
            (245, 245, 245),
        )
        screen.blit(
            label,
            label.get_frect(center=self.BACK_BUTTON.center),
        )
