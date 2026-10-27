
import os
from engine import GameSettings, VigSetting


os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame as pg
import pytest

from ui.craps_app import CrapsApp
from ui.animations import AnimationMode, AnimationSettings


@pytest.fixture
def ui_app(request):
    mode = getattr(
        request,
        "param",
        AnimationMode.INSTANT,
    )

    app = CrapsApp(
        animation_settings=AnimationSettings(
            mode=mode,
        )
    )

    yield app

    pg.quit()


@pytest.fixture
def ui_app_upfront(request):
    mode = getattr(
        request,
        "param",
        AnimationMode.INSTANT,
    )

    app = CrapsApp(
        game_settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        animation_settings=AnimationSettings(
            mode=mode,
        ),
    )

    yield app

    pg.quit()


@pytest.fixture
def ui_app_upfront(request):
    mode = getattr(
        request,
        "param",
        AnimationMode.INSTANT,
    )

    app = CrapsApp(
        game_settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        ),
        animation_settings=AnimationSettings(
            mode=mode,
        ),
    )

    yield app

    pg.quit()