class GameRuleViolation(Exception):
    """A legal game action was attempted at an illegal time."""


class InsufficientFundsError(GameRuleViolation):
    """A player cannot afford the requested transaction."""


class EngineStateError(RuntimeError):
    """An internal engine invariant has been violated."""