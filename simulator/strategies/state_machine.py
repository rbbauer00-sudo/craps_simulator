
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar


StateT = TypeVar("StateT", bound=Enum)


@dataclass
class StateMachine(Generic[StateT]):
    state: StateT
    previous_state: StateT | None = field(
        default=None,
        init=False,
    )
    transition_count: int = field(
        default=0,
        init=False,
    )

    def transition(self, new_state: StateT) -> bool:
        if new_state is self.state:
            return False

        self.previous_state = self.state
        self.state = new_state
        self.transition_count += 1
        return True

    def is_in(self, state: StateT) -> bool:
        return self.state is state
