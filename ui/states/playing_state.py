from __future__ import annotations
import pygame as pg
from .base_state import BaseState
from .roll_phase import RollPhase
from pygame.constants import *
from engine import GameRollResult, Wager, defs, WagerDefinition, WagerType, GameRuleViolation, VigSetting, InsufficientFundsError
from ui.game_elements import DiceSprite, PuckSprite, WagerSprite, PlayerSprite, ChipSprite, VigSprite
from ui.animations.wager_animation_controller import WagerAnimationController
from ui.animations.animation_settings import AnimationMode
from ui.input import CursorTool

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
    COME_BOX_POSITION = (290, 250)

    COME_POSITIONS = {
        4: (170, 190),
        5: (280, 190),
        6: (390, 190),
        8: (500, 190),
        9: (610, 190),
        10: (720, 190),
    }

    BETTING_DEFINITIONS = {
        WagerType.PASS_LINE: (defs.PASS_LINE, None),
        WagerType.DONT_PASS: (defs.DONT_PASS, None),
        WagerType.COME: (defs.COME, None),
        WagerType.PLACE_BET: (defs.PLACE_BET, 6),
        WagerType.LAY_BET: (defs.LAY_BET, 4),
    }

    def __init__(self, app: CrapsApp):
        super().__init__(app)
        self.engine = app.engine

        self.visible_sprites = pg.sprite.Group()
        self.clickable_sprites = pg.sprite.Group()

        self.vig_sprites: dict[Wager, VigSprite] = {}
        self.wager_sprites: dict[Wager, WagerSprite] = {}

        self.selected_tool = CursorTool.CHIP
        self.selected_chip = 25

        # UI elements
        self.chip_buttons = {
            1: pg.FRect(301, 680, 80, 55),
            5: pg.FRect(400, 680, 85, 55),
            10: pg.FRect(495, 680, 85, 55),
            25: pg.FRect(590, 680, 85, 55),
            50: pg.FRect(685, 680, 85, 55),
            100: pg.FRect(780, 680, 85, 55),
        }

        self.tool_buttons = {
            CursorTool.ON: pg.FRect(900, 680, 70, 55),
            CursorTool.OFF: pg.FRect(980, 680, 70, 55),   
        }

        # Game elements
        self.betting_areas = {
            WagerType.PASS_LINE: pg.FRect(390, 505, 120, 70),
            WagerType.DONT_PASS: pg.FRect(540, 505, 120, 70),
            WagerType.COME: pg.FRect(225, 215, 130, 70),
            WagerType.PLACE_BET: pg.FRect(350, 300, 120, 70),
            WagerType.LAY_BET: pg.FRect(110, 340, 120, 70),
        }

        self.pass_odds_area = pg.FRect(
            390, 425, 120, 60
        )



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

        self.player = (
            self.engine.players[0]
            if self.engine.players
            else self.engine.add_player()
        )

        self.player_sprite = PlayerSprite(
            self.player,
            (1000,40),
            self.visible_sprites,
        )

        self.forced_roll_buffer = RollBuffer()
        self.current_roll: GameRollResult | None = None
        self.roll_phase = RollPhase.READY

        self.dealer_position = (
            self.app.screen.get_width() / 2,
            -50,
        )

        self.wager_animator = WagerAnimationController(
            state=self,
            settings=app.animation_settings,
        )


    @property
    def is_animating(self) -> bool:
        return (
            self.roll_phase is not RollPhase.READY
            or self.wager_animator.is_animating
        )

    @property
    def dice_animation_complete(self) -> bool:
        return not self.dice_sprite.is_animating



    def start_wager_animation(self) -> None:
        self.roll_phase = RollPhase.WAGERS_RESOLVING
        self.wager_animator.start()


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
    
   
    def winning_vig_for(self, wager: Wager) -> int:
        if wager not in self.engine.wagers:
            return 0

        wager_type = wager.definition.wager_type

        match wager_type:
            case WagerType.LAY_BET:
                return wager.collected_vig

            case WagerType.PLACE_BET if wager.is_buy:
                return self.engine.calculate_vig(wager)

            case _:
                return 0


    def sync_vig_sprites(self) -> None:
        for wager, parent in self.wager_sprites.items():
            show_indicator = (
                wager.collected_vig > 0
                and not parent.is_animating
                and wager not in self.wager_animator.placing_vig_chips
                and wager not in self.wager_animator.renewing_vig
                and wager not in self.wager_animator.adjusting_vig
            )

            if show_indicator:
                if wager not in self.vig_sprites:
                    self.vig_sprites[wager] = VigSprite(parent)
            else:
                self.vig_sprites.pop(wager, None)

        for wager in list(self.vig_sprites):
            if wager not in self.wager_sprites:
                del self.vig_sprites[wager]

        for sprite in self.vig_sprites.values():
            sprite.update(0.0)


    def sync_wager_sprites(self) -> None:
        active_wagers = set(self.engine.wagers)

        # Remove sprites for resolved wagers.
        for wager, sprite in list(
            self.wager_sprites.items()
        ):
            if wager not in active_wagers:
                sprite.kill()
                del self.wager_sprites[wager]

        # Future: create sprites for wagers
        # introduced outside the UI.

  
    def handle_event(self, event: pg.event.Event) -> None:
        # Escape always works, even during animations.
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.app.running = False
            return

        if self.is_animating:
            return

        match event.type:

            case pg.MOUSEBUTTONDOWN:
                if event.button not in (1, 3):
                    return

                if event.button == 1:
                    if self.handle_chip_click(event.pos):
                        return

                    if self.handle_tool_click(event.pos):
                        return

                    if self.dice_sprite.rect.collidepoint(event.pos):
                        self.roll()
                        return

                wager = self.wager_at_position(event.pos)

                if wager is not None:
                    try:
                        self.apply_wager_tool(
                            wager,
                            event.button,
                        )
                    except (GameRuleViolation, InsufficientFundsError) as exc:
                        print(f"Cannot modify wager: {exc}")

                    return

                if (
                    event.button == 1
                    and self.selected_tool is CursorTool.CHIP
                ):
                    if self.pass_odds_area.collidepoint(event.pos):
                        self.handle_pass_odds_click()
                    else:
                        self.handle_table_click(event.pos)


                        
            case pg.KEYDOWN:
                match event.key:

                    case key if (
                        pg.K_0 <= key <= pg.K_9
                        or key == pg.K_COMMA
                    ):
                        self.forced_roll_buffer.add(event.unicode)

                    case pg.K_BACKSPACE:
                        self.forced_roll_buffer.clear()

                    case pg.K_RETURN:
                        self.roll()


    def handle_table_click(
        self,
        position: tuple[int, int],
    ) -> None:
        for wager_type, rect in self.betting_areas.items():
            if not rect.collidepoint(position):
                continue

            definition, target = self.BETTING_DEFINITIONS[
                wager_type
            ]

            existing = self.engine.get_wager(
                self.player,
                wager_type,
                target=target,
            )

            try:
                self.change_wager(
                    self.selected_chip,
                    wager=existing,
                    definition=definition,
                    target=target,
                    position=rect.center,
                )
            except (GameRuleViolation, InsufficientFundsError) as exc:
                print(f"Cannot change wager: {exc}")

            return


    def draw_selector(
        self,
        screen: pg.Surface,
        rect: pg.FRect,
        label: str,
        selected: bool,
        *,
        ellipse: bool = False,
    ) -> None:
        fill = (
            (35, 105, 185)
            if selected
            else (70, 70, 70)
        )

        border = (
            (245, 245, 245)
            if selected
            else (150, 150, 150)
        )

        if ellipse:
            pg.draw.ellipse(screen, fill, rect)
            pg.draw.ellipse(
                screen,
                border,
                rect,
                width=3 if selected else 1,
            )
        else:
            pg.draw.rect(
                screen,
                fill,
                rect,
                border_radius=8,
            )
            pg.draw.rect(
                screen,
                border,
                rect,
                width=3 if selected else 1,
                border_radius=8,
            )

        text = self.app.font.render(
            label,
            True,
            (255, 255, 255),
        )

        screen.blit(
            text,
            text.get_frect(center=rect.center),
        )

    
    def handle_chip_click(
        self,
        position: tuple[int, int],
    ) -> bool:
        for value, rect in self.chip_buttons.items():
            if rect.collidepoint(position):
                self.selected_chip = value
                self.selected_tool = CursorTool.CHIP
                return True

        return False


    def handle_tool_click(
        self,
        position: tuple[int, int],
    ) -> bool:
        for tool, rect in self.tool_buttons.items():
            if rect.collidepoint(position):
                self.selected_tool = tool
                return True

        return False




    def apply_wager_tool(
        self,
        wager: Wager,
        button: int,
    ) -> None:
        match self.selected_tool:

            case CursorTool.CHIP:
                amount = (
                    self.selected_chip
                    if button == 1
                    else -self.selected_chip
                )
                self.change_wager(amount, wager=wager)

            case CursorTool.ON:
                self.engine.set_wager_working_status(
                    wager, True
                )

            case CursorTool.OFF:
                self.engine.set_wager_working_status(
                    wager, False
                )

            case CursorTool.BUY | CursorTool.PLACE:
                # We'll implement these next.
                pass


    def wager_at_position(
        self,
        position: tuple[int, int],
    ) -> Wager | None:
        for wager, sprite in reversed(
            list(self.wager_sprites.items())
        ):
            if sprite.rect.collidepoint(position):
                return wager

        return None



    def roll(self) -> None:
        if self.is_animating:
            return

        parsed = self.forced_roll_buffer.parse()

        if parsed is None:
            return

        self.player_sprite.sync_bankroll()
        self.player_sprite.auto_sync = False

        self.current_roll = self.engine.roll(*parsed)

        if self.app.animation_settings.mode is AnimationMode.INSTANT:
            # Show the final dice values at their home position.
            self.dice_sprite.show_roll_instant(
                self.current_roll.roll
            )

            # Resolve wager graphics without animation.
            self.start_wager_animation()

            if not self.wager_animator.update():
                raise RuntimeError(
                    "Instant wager resolution did not complete."
                )

            # Position the puck at the engine's new point.
            self.puck_sprite.snap_to(
                self.current_roll.point_after
            )

            # Restore the READY state for the next roll.
            self.finish_roll()
            return

        # Existing animated roll behavior.
        self.roll_phase = RollPhase.DICE_ROLLING
        self.dice_sprite.roll(self.current_roll.roll)


    def take_down_wager(self, wager: Wager) -> None:
        vig_refund = wager.collected_vig

        # Engine enforces all contract restrictions.
        self.engine.take_down_wager(wager)

        # Animate the actual principal and commission return.
        self.wager_animator.remove(
            wager,
            vig_refund,
        )


    def update(self, dt: float) -> None:
        self.visible_sprites.update(dt)
        self.dice_sprite.update(dt)

        wagers_complete = self.wager_animator.update()
        self.sync_vig_sprites()

        match self.roll_phase:
            case RollPhase.READY:
                pass

            case RollPhase.DICE_ROLLING:
                if self.dice_animation_complete:
                    self.start_wager_animation()

            case RollPhase.WAGERS_RESOLVING:
                if wagers_complete:
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


        # Draw Betting Areas
        for wager_type, rect in self.betting_areas.items():
            pg.draw.rect(
                screen,
                (190, 190, 190),
                rect,
                width=2,
                border_radius=6,
            )

            labels = {
                WagerType.PLACE_BET: "PLACE 6",
                WagerType.LAY_BET: "LAY 4",
            }

            label = self.app.font.render(
                labels.get(
                    wager_type,
                    wager_type.name.replace("_", " "),
                ),
                True,
                (230, 230, 230),
            )

            screen.blit(
                label,
                label.get_frect(center=rect.center),
            )

        # Draw puck position labels.
        for point, position in self.puck_sprite.POINT_POSITIONS.items():
            label = "OFF" if point is None else str(point)

            text = self.app.font.render(
                label,
                True,
                (230, 230, 230),
            )

            # Position the label above the puck.
            label_position = (
                position[0],
                position[1] - 45,
            )

            screen.blit(
                text,
                text.get_frect(center=label_position),
            )


        for value, rect in self.chip_buttons.items():
            self.draw_selector(
                screen,
                rect,
                f"${value}",
                selected=(
                    self.selected_tool is CursorTool.CHIP
                    and value == self.selected_chip
                ),
                ellipse=True,
            )

        for tool, rect in self.tool_buttons.items():
            self.draw_selector(
                screen,
                rect,
                tool.name,
                selected=tool is self.selected_tool,
            )

        self.visible_sprites.draw(screen)

        for sprite in self.vig_sprites.values():
            screen.blit(sprite.image, sprite.rect)


    def handle_pass_odds_click(self) -> None:
        parent = self.engine.get_wager(
            self.player,
            WagerType.PASS_LINE,
        )

        if parent is None:
            print("Place a Pass Line wager first.")
            return

        existing = self.engine.get_child_wager(parent)

        try:
            self.change_wager(
                self.selected_chip,
                wager=existing,
                definition=defs.LINE_ODDS,
                parent=parent,
                position=self.pass_odds_area.center,
            )
        except (GameRuleViolation, InsufficientFundsError) as exc:
            print(f"Cannot change Pass Line odds: {exc}")       


    def change_wager(
        self,
        amount: int,
        *,
        wager: Wager | None = None,
        definition: WagerDefinition | None = None,
        target: int | None = None,
        position: tuple[float, float] | None = None,
        parent: Wager | None = None,
    ) -> None:
        if self.is_animating or amount == 0:
            return

        # No existing wager: create a new wager.
        if wager is None:
            if amount < 0:
                return

            if definition is None or position is None:
                raise ValueError(
                    "New wagers require a definition and position."
                )

            wager = Wager(
                definition=definition,
                player=self.player,
                game=self.engine,
                value=amount,
                target=target,
                parent_wager=parent,
            )

            self.engine.place_wager(wager)
            self.wager_animator.place(wager, position)
            return

        # Existing wager: request complete removal.
        if amount < 0 and -amount >= wager.value:
            # Removal can also refund associated odds.
            child = self.engine.get_child_wager(wager)

            refunded = [
                (item, item.collected_vig)
                for item in (wager, child)
                if item is not None
            ]

            self.engine.take_down_wager(wager)

            for item, vig_refund in refunded:
                self.wager_animator.remove(
                    item,
                    vig_refund,
                )

            return

        # Existing wager: increase or decrease.
        sprite = self.wager_sprites[wager]
        old_vig = wager.collected_vig

        sprite.auto_sync_value = False

        try:
            if amount > 0:
                self.engine.increase_wager(wager, amount)
            else:
                self.engine.decrease_wager(wager, -amount)
        except Exception:
            sprite.auto_sync_value = True
            raise

        vig_change = wager.collected_vig - old_vig

        self.wager_animator.adjust(
            wager,
            amount,
            vig_change,
        )

