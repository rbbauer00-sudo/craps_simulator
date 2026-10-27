
import pygame as pg

from engine import defs, WagerType
from ui.input import BettingArea, CursorTool


class TableLayout:
    BOX_NUMBERS = (4, 5, 6, 8, 9, 10)

    TABLE_RECT = pg.FRect(20, 20, 940, 580)
    SIDEBAR_RECT = pg.FRect(980, 20, 280, 580)
    CONTROLS_RECT = pg.FRect(20, 620, 1240, 160)

    # Main table: six columns, seven rows.
    GRID_X = 40
    GRID_Y = 105
    CELL_W = 110
    CELL_H = 48
    GRID_DX = 125
    GRID_DY = 60

    # Sidebar: two columns, seven rows.
    SIDE_X = 990
    SIDE_Y = 125
    SIDE_W = 125
    SIDE_H = 48
    SIDE_DX = 135
    SIDE_DY = 65

    # Game elements
    DICE_POSITION = (815, 480)
    DEALER_POSITION = (640, -50)
    PLAYER_POSITION = (990, 40)
    BONUS_PROGRESS_POSITION = (790, 225)

    @classmethod
    def cell(cls, column: int, row: int) -> pg.FRect:
        return pg.FRect(
            cls.GRID_X + column * cls.GRID_DX,
            cls.GRID_Y + row * cls.GRID_DY,
            cls.CELL_W,
            cls.CELL_H,
        )

    @classmethod
    def side_cell(cls, column: int, row: int) -> pg.FRect:
        return pg.FRect(
            cls.SIDE_X + column * cls.SIDE_DX,
            cls.SIDE_Y + row * cls.SIDE_DY,
            cls.SIDE_W,
            cls.SIDE_H,
        )

    # Wager travel locations.
    COME_POSITIONS = {
        number: (95 + index * 125, 189)
        for index, number in enumerate(BOX_NUMBERS)
    }

    DONT_COME_POSITIONS = {
        number: (95 + index * 125, 249)
        for index, number in enumerate(BOX_NUMBERS)
    }

    PUCK_POSITIONS = {
        number: (95 + index * 125, 65)
        for index, number in enumerate(BOX_NUMBERS)
    }
    PUCK_POSITIONS[None] = (850, 65)

    @classmethod
    def travel_position(
        cls,
        wager_type: WagerType,
        target: int,
    ) -> tuple[int, int]:
        match wager_type:
            case WagerType.COME:
                positions = cls.COME_POSITIONS

            case WagerType.DONT_COME:
                positions = cls.DONT_COME_POSITIONS

            case _:
                raise ValueError(
                    f"No travel position for {wager_type}"
                )

        return positions[target]

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
        CursorTool.BUY: pg.FRect(1060, 680, 85, 55),
        CursorTool.PLACE: pg.FRect(1150, 680, 85, 55),
    }

    @classmethod
    def create_betting_areas(cls) -> list[BettingArea]:
        areas = []

        # Number-specific bets.
        for column, number in enumerate(cls.BOX_NUMBERS):
            areas.extend([
                BettingArea(
                    f"COME {number} ODDS",
                    cls.cell(column, 0),
                    defs.LINE_ODDS,
                    parent_type=WagerType.COME,
                    parent_target=number,
                ),
                BettingArea(
                    f"DC {number} ODDS",
                    cls.cell(column, 3),
                    defs.LAY_ODDS,
                    parent_type=WagerType.DONT_COME,
                    parent_target=number,
                ),
                BettingArea(
                    f"PLACE {number}",
                    cls.cell(column, 4),
                    defs.PLACE_BET,
                    target=number,
                ),
                BettingArea(
                    f"LAY {number}",
                    cls.cell(column, 5),
                    defs.LAY_BET,
                    target=number,
                ),
            ])

        # Basic wagers.
        basic_bets = (
            ("PASS LINE", defs.PASS_LINE, None),
            ("DON'T PASS", defs.DONT_PASS, None),
            ("COME", defs.COME, None),
            ("DON'T COME", defs.DONT_COME, None),
            ("PASS ODDS", defs.LINE_ODDS, WagerType.PASS_LINE),
            ("DP ODDS", defs.LAY_ODDS, WagerType.DONT_PASS),
        )

        for column, (name, definition, parent_type) in enumerate(
            basic_bets
        ):
            areas.append(
                BettingArea(
                    name,
                    cls.cell(column, 6),
                    definition,
                    parent_type=parent_type,
                )
            )

        areas.append(
            BettingArea(
                "FIELD",
                cls.cell(0, 7),
                defs.FIELD,
            )
        )

        # Bonus bets, hardways and propositions.
        sidebar_bets = (
            ("ATS SMALL", defs.ATS_SMALL),
            ("ATS TALL", defs.ATS_TALL),
            ("ATS ALL", defs.ATS_ALL),
            ("FIRE", defs.FIRE_BET),
            ("HARD 4", defs.HARDWAY),
            ("HARD 6", defs.HARDWAY),
            ("HARD 8", defs.HARDWAY),
            ("HARD 10", defs.HARDWAY),
            ("ANY SEVEN", defs.ANY_SEVEN),
            ("ANY CRAPS", defs.ANY_CRAPS),
            ("YO", defs.YO_LEVEN),
            ("ACE DEUCE", defs.ACE_DEUCE),
            ("DEUCE", defs.DEUCE),
            ("MIDNIGHT", defs.MIDNIGHT),
        )

        for index, (name, definition) in enumerate(sidebar_bets):
            target = (
                int(name.split()[-1])
                if name.startswith("HARD ")
                else None
            )

            areas.append(
                BettingArea(
                    name,
                    cls.side_cell(index % 2, index // 2),
                    definition,
                    target=target,
                )
            )

        return areas
