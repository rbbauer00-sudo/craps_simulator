import pygame as pg
from .base_state import BaseState


class GameMenuState(BaseState):
    transparent = True

    def handle_event(self, event: pg.event.Event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.app.states.pop()

            elif event.key == pg.K_q:
                self.app.running = False

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        shade = pg.Surface(screen.get_size(), pg.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        screen.blit(shade, (0, 0))
        rect = pg.Rect(390, 200, 500, 400)
        pg.draw.rect(screen, (65, 65, 65), rect, border_radius=10)
        pg.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=10)
        label = self.app.font.render("GAME MENU - ESC to resume", True, (255, 255, 255))
        screen.blit(label, label.get_rect(center=rect.center))
