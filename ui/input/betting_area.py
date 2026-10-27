
from dataclasses import dataclass

import pygame as pg

from engine import WagerDefinition, WagerType


@dataclass
class BettingArea:
    name: str
    rect: pg.FRect
    definition: WagerDefinition
    target: int | None = None

    # Only used for wagers requiring a parent.
    parent_type: WagerType | None = None
    parent_target: int | None = None

    @property
    def requires_parent(self) -> bool:
        return self.parent_type is not None
