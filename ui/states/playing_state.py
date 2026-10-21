from __future__ import annotations
import pygame as pg
from .base_state import BaseState
from ui.game_elements.dice_sprite import DiceSprite
from pygame.constants import *


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui import CrapsApp
    from engine import Game as GameEngine


def add_char(char: str, chars: str) -> str:
    candidate = chars + char

    if char == ",":
        # Allow comma only after a single 1-6
        if len(chars) == 1 and chars in "123456":
            return candidate

    elif char in "0123456789":
        # Only allow digits 1-6 to follow a comma
        if "," in chars:
            if len(chars) == 2 and char in "123456":
                return candidate

        # If no comma, allow any digit that results in a total of 1-12
        elif (candidate in map(str, range(1, 13))):
            return candidate

    # return original string if new char is invalid
    return chars

def parse_forced_roll_buffer(
    buffer: str,
) -> tuple[int | None, int | None]:
    if not buffer:
        return None, None

    parts = buffer.split(",", maxsplit=1)

    d1 = int(parts[0]) if parts[0] else None
    d2 = int(parts[1]) if len(parts) > 1 and parts[1] else None

    return d1, d2
    

class PlayingState(BaseState):
    def __init__(self, game: CrapsApp):
        self.game = game
        self.game_engine

        self.visible_sprites = pg.sprite.Group()
        self.clickable_sprites = pg.sprite.Group()

        # Game elements
        self.dice_sprite = DiceSprite(
            size= 50,
            topleft=(150,500),
            game=game,
            clickable_sprites=self.clickable_sprites,
            visible_sprites=self.visible_sprites,
        )   

        self.forced_roll_buffer: str = ""
        
        self.is_animating: bool = False

    def handle_event(self, event: pg.event.Event):
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                from .game_menu_state import GameMenuState
                self.app.states.push(GameMenuState(self.app))
            elif (
                event.key in range(K_0, K_9 + 1)
                or event.key == K_COMMA
            ):
                self.forced_roll_buffer = add_char(
                    event.unicode,
                    self.forced_roll_buffer
                )
            
            elif event.key == K_BACKSPACE:
                self.forced_roll_buffer = ""
            
            elif event.key == K_RETURN:
                d1, d2 = parse_forced_roll_buffer(
                    self.forced_roll_buffer,
                )
                self.forced_roll_buffer = ""
                self.roll(d1, d2)

    def roll(
        self, 
        d1: int = None, 
        d2: int = None,
    ) -> None:
        game_result = self.game.roll()
        


    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        screen.fill((30, 30, 30))

        # Temporary rectangles
        pg.draw.rect(screen, (30, 90, 50), (20, 20, 940, 580))
        pg.draw.rect(screen, (55, 55, 55), (980, 20, 280, 580))
        pg.draw.rect(screen, (55, 55, 55), (20, 620, 1240, 160))

        self.visible_sprites.draw(screen)
