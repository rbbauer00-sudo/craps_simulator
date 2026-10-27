
import pygame as pg

from engine import defs, WagerType
from ui.input import BettingArea


class TableLayout:
    COME_BOX_POSITION = (290, 250)

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
                pg.FRect(225, 215, 130, 70),
                defs.COME,
            ),
            BettingArea(
                "PLACE 6",
                pg.FRect(350, 300, 120, 70),
                defs.PLACE_BET,
                target=6,
            ),
            BettingArea(
                "LAY 4",
                pg.FRect(110, 340, 120, 70),
                defs.LAY_BET,
                target=4,
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

        return areas
