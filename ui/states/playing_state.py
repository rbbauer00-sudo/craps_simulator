from __future__ import annotations
import pygame as pg
from .base_state import BaseState
from ui.game_elements.dice_sprite import DiceSprite
from ui.game_elements.puck_sprite import PuckSprite
from .roll_phase import RollPhase
from pygame.constants import *
from engine import GameRollResult


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui import CrapsApp
    from engine import Game as GameEngine

class RollBuffer:
    def __init__(self):
        self.buffer: str = ""

    def add(self, char: str) -> None:
        candidate = self.buffer + char

        if char == ",":
            # Allow comma only after a single 1-6
            if len(self.buffer) == 1 and self.buffer in "123456":
                self.buffer = candidate

        elif char in "0123456789":
            # Only allow digits 1-6 to follow a comma
            if "," in self.buffer:
                if len(self.buffer) == 2 and char in "123456":
                    self.buffer = candidate

            # If no comma, allow any digit that results in a total of 1-12
            elif (candidate in map(str, range(1, 13))):
                self.buffer = candidate


    def parse(self) -> tuple[int | None] | None:
        buffer = self.buffer
        self.clear()

        if not buffer:
            return None, None

        try:
            parts = buffer.split(",")

            if len(parts) == 1:
                total = int(parts[0])
                if 2 <= total <= 12:
                    return total, None

            elif len(parts) == 2:
                d1, d2 = map(int, parts)
                if 1 <= d1 <= 6 and 1 <= d2 <= 6:
                    return d1, d2

        except ValueError:
            pass

        return None

    def clear(self) -> None:
        self.buffer = ""
        


class PlayingState(BaseState):
    def __init__(self, app: CrapsApp):
        super().__init__(app)
        self.engine = app.engine

        self.visible_sprites = pg.sprite.Group()
        self.clickable_sprites = pg.sprite.Group()

        # Game elements
        self.dice_sprite = DiceSprite(
            size= 50,
            topleft=(150,500),
            app=app,
            clickable_sprites=self.clickable_sprites,
            visible_sprites=self.visible_sprites,
        )   

        self.puck_sprite = PuckSprite(
            self.engine.point,
            self.visible_sprites,
        )

        self.forced_roll_buffer = RollBuffer()
        self.current_roll: GameRollResult | None = None
        self.roll_phase = RollPhase.READY

    @property
    def is_animating(self) -> bool:
        return self.roll_phase is not RollPhase.READY

    @property
    def dice_animation_complete(self) -> bool:
        return not self.dice_sprite.is_animating


    def start_wager_animation(self) -> None:
        self.roll_phase = RollPhase.WAGERS_RESOLVING
        #TODO: wager animation

    @property
    def wager_animation_complete(self) -> bool:
        #TODO: write return logic
        return True

    def start_puck_animation(self) -> None:
        self.roll_phase = RollPhase.PUCK_MOVING

        if self.current_roll is None:
            raise RuntimeError("No current roll to resolve.")

        self.puck_sprite.on_roll(
            self.current_roll.point_before,
            self.current_roll.point_after,
        )

    @property
    def puck_animation_complete(self) -> bool:
        return not self.puck_sprite.is_animating


    def start_dice_return(self) -> None:
        self.roll_phase = RollPhase.DICE_RETURNING
        self.dice_sprite.start_return()
    
    @property
    def dice_return_complete(self) -> bool:
        return not self.dice_sprite.is_returning




    def finish_roll(self) -> None:
        self.current_roll = None
        self.roll_phase = RollPhase.READY

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            from .game_menu_state import GameMenuState
            self.app.states.push(GameMenuState(self.app))
            return

        if self.is_animating:
            return

        if event.type == pg.KEYDOWN:
            if event.key in range(pg.K_0, pg.K_9 + 1) or event.key == pg.K_COMMA:
                self.forced_roll_buffer.add(event.unicode)

            elif event.key == pg.K_BACKSPACE:
                self.forced_roll_buffer.clear()

            elif event.key == pg.K_RETURN:
                self.roll()

        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.dice_sprite.rect.collidepoint(event.pos):
                    self.roll()


    def roll(self) -> None:
        if self.is_animating:
            return
        
        parsed = self.forced_roll_buffer.parse() 
        
        if parsed is None:
            return

        self.current_roll = self.engine.roll(*parsed)
        self.roll_phase = RollPhase.DICE_ROLLING
        
        self.dice_sprite.roll(self.current_roll.roll)


    def update(self, dt: float):
        self.visible_sprites.update(dt)
        self.dice_sprite.update(dt)

        match self.roll_phase:
            case RollPhase.READY:
                pass

            case RollPhase.DICE_ROLLING:
                if self.dice_animation_complete:
                    self.start_wager_animation()

            case RollPhase.WAGERS_RESOLVING:
                if self.wager_animation_complete:
                    self.start_puck_animation()

            case RollPhase.PUCK_MOVING:
                if self.puck_animation_complete:
                    self.start_dice_return()

            case RollPhase.DICE_RETURNING:
                if self.dice_return_complete:
                    self.finish_roll()





    def draw(self, screen: pg.Surface):
        screen.fill((30, 30, 30))

        # Temporary rectangles
        pg.draw.rect(screen, (30, 90, 50), (20, 20, 940, 580))
        pg.draw.rect(screen, (55, 55, 55), (980, 20, 280, 580))
        pg.draw.rect(screen, (55, 55, 55), (20, 620, 1240, 160))

        self.visible_sprites.draw(screen)
