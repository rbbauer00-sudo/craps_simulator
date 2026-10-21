import pygame as pg

from ui.states.base_state import BaseState


class StateStack:
    def __init__(self):
        self._stack: list[BaseState] = []

    @property
    def current(self) -> BaseState | None:
        return self._stack[-1] if self._stack else None

    def push(self, state: BaseState):
        if self.current:
            self.current.pause()
        self._stack.append(state)
        state.enter()

    def pop(self) -> BaseState | None:
        if not self._stack:
            return None
        state = self._stack.pop()
        state.exit()
        if self.current:
            self.current.resume()
        return state

    def replace(self, state: BaseState):
        # Replace without temporarily resuming the state beneath.
        if self._stack:
            old = self._stack.pop()
            old.exit()
        self._stack.append(state)
        state.enter()

    def clear(self):
        while self._stack:
            self._stack.pop().exit()

    def reset(self, state: BaseState):
        self.clear()
        self.push(state)

    def handle_event(self, event: pg.event.Event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt: float):
        if self.current:
            self.current.update(dt)

    def draw(self, screen: pg.Surface):
        if not self._stack:
            return
        start = len(self._stack) - 1
        while start > 0 and self._stack[start].transparent:
            start -= 1
        for state in self._stack[start:]:
            state.draw(screen)
