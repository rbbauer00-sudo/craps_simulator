
import os

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
