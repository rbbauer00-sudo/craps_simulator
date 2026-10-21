"""Future title menu; not wired into the app yet."""
import pygame as pg
from .base_state import BaseState


class TitleState(BaseState):
    def handle_event(self, event: pg.event.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        screen.fill((25, 35, 40))
        text = self.app.font.render("Craps Simulator - Title (placeholder)", True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=screen.get_rect().center))
