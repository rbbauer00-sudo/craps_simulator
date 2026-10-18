from dataclasses import dataclass, field
from . import constants as const
import random


def format_seed(value: int) -> str:
    if type(value) is not int or not 0 <= value < 2**64:
        raise ValueError(
            "Dice seed must be an unsigned 64-bit integer; "
            f"received {value!r}."
        )

    if value == 0:
        encoded = const.BASE32[0]
    else:
        chars = []

        while value:
            value, remainder = divmod(value, len(const.BASE32))
            chars.append(const.BASE32[remainder])

        encoded = ''.join(reversed(chars))

    return '-'.join(
        encoded[i:i + 4]
        for i in range(0, len(encoded), 4)
    )


def parse_seed(value: str) -> int:
    if type(value) is not str:
        raise TypeError(
            "parse_seed() requires a str; "
            f"received {type(value).__name__}: {value!r}."
        )
    
    value = value.replace('-', '').upper()

    result = 0

    for char in value:
        if char not in const.BASE32:
            raise ValueError(f'Invalid const.BASE32 character: {char}')

        result = result * len(const.BASE32) + const.BASE32.index(char)

    return result


def convert_total_to_tuple(total: int):
    """
    Returns a random pair of dice equal to the 
    supplied total value.  Intended for use when
    a roll total is needed, but the individual 
    die values do not matter.  RNG for this method
    is intentionally generic so as not to consume
    seeded rolls.
    """

    if not 2 <= total <= 12:
        msg = 'Invalid total: must be between 2 and 12.'
        raise ValueError(msg)
    
    d2min = max(1, total - 6)
    d2max = min(6, total - 1)

    d2 = random.randint(d2min, d2max)
    d1 = total - d2

    return d1, d2


@dataclass(frozen=True)
class RollResult:
    d1: int
    d2: int | None = field(default = None)
    total: int | None = field(init=False)
    as_tuple: tuple[int, int] | None = field(init=False)


    def __post_init__(self):
        # If only sum given, generate random pair
        if self.d2 is None:
            d1, d2 = convert_total_to_tuple(self.d1)

            object.__setattr__(self, 'd1', d1)
            object.__setattr__(self, 'd2', d2)

        if not all(
            type(die) is int and 1 <= die <= 6
            for die in (self.d1, self.d2)
        ):
            raise ValueError(
                f"Invalid dice faces ({self.d1!r}, {self.d2!r}); "
                "each die must be an integer from 1 to 6."
            )

        object.__setattr__(
            self, 
            "total", 
            (self.d1 + self.d2),
        )
        
        object.__setattr__(
            self, 
            "as_tuple", 
            tuple(sorted((self.d1, self.d2)))
        )


    def __str__(self):
        return(
            f"RollResult: {self.d1},{self.d2} = {self.total}"
        )


class Dice:
    def __init__(
            self,
            seed: int | str | None = None,
            predetermined_rolls: list[
                int | tuple[int,int] | RollResult
            ] | None = None,
    ) -> None:

        self._history: list[RollResult] = []

        #RNG seed
        if seed is None:
            seed = random.SystemRandom().randrange(2**64)
        
        elif isinstance(seed, str):
            seed = parse_seed(seed)

        formatted_seed = format_seed(seed)

        # Format predetermined roll list
        rolls: list[tuple[int, int]] = []
        
        if predetermined_rolls is not None:
            for index, roll in enumerate(predetermined_rolls):

                if type(roll) is int:
                   d1, d2 = convert_total_to_tuple(roll)

                elif isinstance(roll, RollResult):
                   d1, d2 = roll.as_tuple

                elif (
                    isinstance(roll, tuple)
                    and len(roll) == 2
                ):
                    d1, d2 = roll
                    
                else:
                    raise TypeError(
                        "Invalid predetermined roll at index "
                        f"{index}: {roll!r}. Expected an integer "
                        "total, a two-element tuple, or RollResult."
                    )

                if not all(
                    type(die) is int and 1 <= die <= 6
                    for die in (d1, d2)
                ):
                    raise ValueError(
                        "Invalid predetermined roll at index "
                        f"{index}: ({d1!r}, {d2!r}). "
                        "Dice must be integers from 1 to 6."
                    )

                rolls.append((d1, d2))

        # Reverse roll list so pop() pulls from correct end
        self._predetermined_rolls: list[
            tuple[int, int]
        ] = list(reversed(rolls))

        # Store seed values as attributes
        self.seed = seed
        self.formatted_seed = formatted_seed
        self.rng = random.Random(seed)


    def get_history(self) -> list[RollResult]:
        return tuple(self._history)


    def get_last_roll(self) -> RollResult:
        return (
            self._history[-1] 
            if self._history 
            else None
        )


    def roll(
        self,
        d1: int | None = None,
        d2: int | None = None,
    ) -> RollResult:

        # Validate argument combinations
        if d1 is None and d2 is not None:
            raise ValueError(
                "d2 cannot be supplied without d1."
            )

        if d1 is not None:
            if type(d1) is not int:
                raise TypeError(
                    "d1 must be an integer; "
                    f"received {type(d1).__name__}: {d1!r}."
                )

            if d2 is not None:
                if type(d2) is not int:
                    raise TypeError(
                        "d2 must be an integer; "
                        f"received {type(d2).__name__}: {d2!r}."
                    )

                if not (
                    1 <= d1 <= 6
                    and 1 <= d2 <= 6
                ):
                    raise ValueError(
                        f"Invalid forced roll: ({d1}, {d2}). "
                        "Dice must be between 1 and 6."
                    )

            elif not 2 <= d1 <= 12:
                raise ValueError(
                    f"Invalid forced total: {d1}. "
                    "Total must be between 2 and 12."
                )

        # Input has passed validation.
        # Consume one RNG roll to maintain synchronization.
        random_roll = (
            self.rng.randint(1, 6),
            self.rng.randint(1, 6),
        )

        # Forced dice faces
        if d1 is not None and d2 is not None:
            pass

        # Forced total
        elif d1 is not None:
            d1, d2 = convert_total_to_tuple(d1)

        # Predetermined roll
        elif self._predetermined_rolls:
            d1, d2 = self._predetermined_rolls.pop()

        # Random roll
        else:
            d1, d2 = random_roll

        result = RollResult(d1, d2)
        self._history.append(result)

        return result
