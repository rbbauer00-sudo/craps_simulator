"""Simple modal message overlay; push it onto the state stack."""
import pygame as pg
from .base_state import BaseState


class MessageState(BaseState):
    transparent = True

    def __init__(self, app, message: str = "Message"):
        super().__init__(app)
        self.message = message

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN and event.key in (pg.K_ESCAPE, pg.K_RETURN):
            self.app.states.pop()

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        shade = pg.Surface(screen.get_size(), pg.SRCALPHA)
        shade.fill((0, 0, 0, 130))
        screen.blit(shade, (0, 0))
        rect = pg.Rect(390, 270, 500, 260)
        pg.draw.rect(screen, (65, 65, 65), rect, border_radius=10)
        pg.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=10)
        text = self.app.font.render(self.message, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=rect.center))
