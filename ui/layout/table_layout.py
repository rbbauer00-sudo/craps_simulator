
import pygame as pg

from engine import defs, WagerType
from ui.input import BettingArea,CursorTool


class TableLayout:

    COME_POSITIONS = {
        4: (170, 190),
        5: (280, 190),
        6: (390, 190),
        8: (500, 190),
        9: (610, 190),
        10: (720, 190),
    }

    PUCK_POSITIONS = {
        4: (170, 65),
        5: (280, 65),
        6: (390, 65),
        8: (500, 65),
        9: (610, 65),
        10: (720, 65),
        None: (850, 65),
    }

    DICE_POSITION = (150, 500)
    DEALER_POSITION = (640, -50)

    PLAYER_POSITION = (1000, 40)

    CHIP_BUTTONS = {
        1: pg.FRect(301, 680, 80, 55),
        5: pg.FRect(400, 680, 85, 55),
        10: pg.FRect(495, 680, 85, 55),
        25: pg.FRect(590, 680, 85, 55),
        50: pg.FRect(685, 680, 85, 55),
        100: pg.FRect(780, 680, 85, 55),
    }

    TOOL_BUTTONS = {
        CursorTool.ON: pg.FRect(900, 680, 70, 55),
        CursorTool.OFF: pg.FRect(980, 680, 70, 55),
    }

    TABLE_RECT = pg.FRect(20, 20, 940, 580)
    SIDEBAR_RECT = pg.FRect(980, 20, 280, 580)
    CONTROLS_RECT = pg.FRect(20, 620, 1240, 160)

    @classmethod
    def create_betting_areas(cls) -> list[BettingArea]:
        areas = [
            BettingArea(
                "PASS LINE",
                pg.FRect(390, 505, 120, 70),
                defs.PASS_LINE,
            ),
            BettingArea(
                "DON'T PASS",
                pg.FRect(540, 505, 120, 70),
                defs.DONT_PASS,
            ),
            BettingArea(
                "COME",
                pg.FRect(225, 425, 130, 60),
                defs.COME,
            ),
            BettingArea(
                "PASS ODDS",
                pg.FRect(390, 425, 120, 60),
                defs.LINE_ODDS,
                parent_type=WagerType.PASS_LINE,
            ),
            BettingArea(
                "DP ODDS",
                pg.FRect(680, 505, 110, 70),
                defs.LAY_ODDS,
                parent_type=WagerType.DONT_PASS,
            ),
        ]

        for number, (x, y) in cls.COME_POSITIONS.items():
            areas.append(
                BettingArea(
                    f"COME {number} ODDS",
                    pg.FRect(x - 45, y - 95, 90, 45),
                    defs.LINE_ODDS,
                    parent_type=WagerType.COME,
                    parent_target=number,
                )
            )

        for number, (x, _) in cls.COME_POSITIONS.items():
            areas.extend([
                BettingArea(
                    f"PLACE {number}",
                    pg.FRect(x - 45, 300, 90, 45),
                    defs.PLACE_BET,
                    target=number,
                ),
                BettingArea(
                    f"LAY {number}",
                    pg.FRect(x - 45, 365, 90, 45),
                    defs.LAY_BET,
                    target=number,
                ),
            ])

        return areas
