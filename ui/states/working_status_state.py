
import pygame as pg

from .base_state import BaseState


class WorkingStatusState(BaseState):
    transparent = True

    PANEL = pg.FRect(390, 150, 500, 500)

    PLACE_BUTTON = pg.FRect(440, 260, 400, 70)
    HARDWAY_BUTTON = pg.FRect(440, 355, 400, 70)
    BACK_BUTTON = pg.FRect(490, 545, 300, 60)

    def __init__(self, app, playing_state=None):
        super().__init__(app)

        self.playing = playing_state

        self.title_font = pg.font.SysFont(
            None, 40, bold=True
        )
        self.font = pg.font.SysFont(None, 27)
        self.small_font = pg.font.SysFont(None, 21)

    @property
    def can_change_working(self) -> bool:
        return (
            self.playing is None
            or not self.playing.is_animating
        )

    def toggle_place(self):
        if not self.can_change_working:
            return

        preferences = self.app.working_preferences
        preferences.place_on_comeout = (
            not preferences.place_on_comeout
        )

        self.apply_current_defaults()

    def toggle_hardway(self):
        if not self.can_change_working:
            return

        preferences = self.app.working_preferences
        preferences.hardway_on_comeout = (
            not preferences.hardway_on_comeout
        )

        self.apply_current_defaults()

    def apply_current_defaults(self):
        if self.playing is not None:
            self.playing.apply_working_defaults()

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

        elif self.PLACE_BUTTON.collidepoint(event.pos):
            self.toggle_place()

        elif self.HARDWAY_BUTTON.collidepoint(event.pos):
            self.toggle_hardway()

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
            "WORKING STATUS",
            True,
            (245, 245, 245),
        )

        screen.blit(
            title,
            title.get_frect(
                center=(640, 195)
            ),
        )

        subtitle = self.small_font.render(
            "Default wager status during comeout",
            True,
            (200, 200, 200),
        )
        screen.blit(
            subtitle,
            subtitle.get_frect(center=(640, 230)),
        )

        preferences = self.app.working_preferences
        enabled = self.can_change_working

        for rect, label, working in (
            (
                self.PLACE_BUTTON,
                "PLACE / BUY",
                preferences.place_on_comeout,
            ),
            (
                self.HARDWAY_BUTTON,
                "HARDWAYS",
                preferences.hardway_on_comeout,
            ),
        ):
            color = (
                (45, 105, 75)
                if working else (105, 75, 45)
            ) if enabled else (65, 65, 65)

            pg.draw.rect(
                screen,
                color,
                rect,
                border_radius=8,
            )

            foreground = (
                (245, 245, 245)
                if enabled else (145, 145, 145)
            )

            name = self.font.render(
                label,
                True,
                foreground,
            )
            status = self.small_font.render(
                "ON DURING COMEOUT"
                if working else "OFF DURING COMEOUT",
                True,
                foreground,
            )

            screen.blit(
                name,
                name.get_frect(
                    center=(rect.centerx, rect.centery - 13)
                ),
            )
            screen.blit(
                status,
                status.get_frect(
                    center=(rect.centerx, rect.centery + 15)
                ),
            )

        if not enabled:
            message = self.small_font.render(
                "Finish the current roll to change defaults",
                True,
                (220, 180, 120),
            )
            screen.blit(
                message,
                message.get_frect(center=(640, 485)),
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
            back.get_frect(center=self.BACK_BUTTON.center),
        )
