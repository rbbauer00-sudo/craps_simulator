from enum import Enum, auto

class Resolution(Enum):
    WIN = auto()
    LOSE = auto()
    PUSH = auto()
    MOVE = auto()
    NONE = auto()
    REMOVE = auto()


class WagerType(Enum):
    TEST_WAGER = auto()

    ANY_SEVEN = auto()
    ANY_CRAPS = auto()
    MIDNIGHT = auto()
    DEUCE = auto()
    ACE_DEUCE = auto()
    YO_LEVEN = auto()
    HOP = auto()
    HORN = auto()
    FIELD = auto()
    HARDWAY = auto()

    COME = auto()
    DONT_COME = auto()
    PASS_LINE = auto()
    DONT_PASS = auto()

    LINE_ODDS = auto()
    LAY_ODDS = auto()
    
    PLACE_BET = auto()
    LAY_BET =  auto()
    
    ATS_ALL = auto()
    ATS_SMALL = auto()
    ATS_TALL = auto()
    FIRE_BET = auto()


class VigSetting(Enum):
    UP_FRONT = auto()
    ON_WIN = auto()
    AUTO_BUY = auto()