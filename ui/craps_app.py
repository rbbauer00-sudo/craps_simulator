
import pygame as pg

from engine import GameEngine, GameSettings
from ui.state_stack import StateStack
from ui.states.playing_state import PlayingState
from ui.animations import AnimationSettings

class CrapsApp:
    WIDTH = 1280
    HEIGHT = 800
    FPS = 60

    def __init__(
        self,
        game_settings: GameSettings | None = None,
        animation_settings: AnimationSettings | None = None,
    ):
        pg.init()

        self.animation_settings = animation_settings or AnimationSettings()
    
        self.screen = pg.display.set_mode((self.WIDTH, self.HEIGHT))
        pg.display.set_caption("Craps Simulator")
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont(None, 28)
        self.small_font = pg.font.SysFont(None, 16)
        self.running = False

        # Engine integration can be added when roll controls are built.
        self.engine = GameEngine(settings=game_settings)
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

    def set_animation_settings(
        self,
        settings: AnimationSettings,
    ) -> None:
        state = self.states.current

        if state.is_animating:
            raise RuntimeError(
                "Cannot change animation settings during an animation."
            )

        self.animation_settings = settings
        state.wager_animator.settings = settings
