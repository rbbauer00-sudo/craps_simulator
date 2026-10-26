
import pygame as pg

from engine import GameEngine, GameSettings
from ui.state_stack import StateStack
from ui.states.playing_state import PlayingState

class CrapsApp:
    WIDTH = 1280
    HEIGHT = 800
    FPS = 60

    def __init__(
        self,
        settings: GameSettings | None = None
    ):
        pg.init()
        self.screen = pg.display.set_mode((self.WIDTH, self.HEIGHT))
        pg.display.set_caption("Craps Simulator")
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont(None, 28)
        self.running = False

        # Engine integration can be added when roll controls are built.
        self.engine = GameEngine(settings=settings)
        self.states = StateStack()
        self.states.push(PlayingState(self))

    def run(self):
        self.running = True
        try:
            while self.running:
                dt = self.clock.tick(self.FPS) / 1000.0
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        self.running = False
                    else:
                        self.states.handle_event(event)

                self.states.update(dt)
                self.screen.fill((30, 30, 30))
                self.states.draw(self.screen)
                pg.display.flip()
        finally:
            pg.quit()

