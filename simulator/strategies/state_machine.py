from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar


StateT = TypeVar("StateT", bound=Enum)


@dataclass
class Transition(Generic[StateT]):
    source: StateT
    target: StateT
    event: str
    guard: Callable | None = None


class StateMachine(Generic[StateT]):

    def __init__(self, initial_state: StateT):
        self.state = initial_state
        self.transitions: list[Transition[StateT]] = []

    def add_transition(
        self,
        source: StateT,
        target: StateT,
        event: str,
        guard: Callable | None = None,
    ) -> None:

        self.transitions.append(
            Transition(source, target, event, guard)
        )

    def trigger(self, event: str, ctx=None) -> bool:

        for transition in self.transitions:

            if transition.source != self.state:
                continue

            if transition.event != event:
                continue

            if (
                transition.guard is not None
                and not transition.guard(ctx)
            ):
                continue

            self.state = transition.target
            return True

        return False