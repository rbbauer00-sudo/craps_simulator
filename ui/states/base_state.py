from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import pygame as pg

if TYPE_CHECKING:
    from ui.craps_app import CrapsApp


class BaseState(ABC):
    transparent = False

    def __init__(self, app: "CrapsApp"):
        self.app = app

    def enter(self):
        pass

    def exit(self):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    @abstractmethod
    def handle_event(self, event: pg.event.Event):
        pass

    @abstractmethod
    def update(self, dt: float):
        pass

    @abstractmethod
    def draw(self, screen: pg.Surface):
        pass
