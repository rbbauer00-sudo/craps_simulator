from ui import CrapsApp, AnimationSettings, AnimationMode
from engine import GameSettings, VigSetting

def main():
    game_settings = GameSettings(
        buy_vig_setting=VigSetting.AUTO_BUY
    )

    animation_settings = AnimationSettings(
        mode=AnimationMode.MINIMAL,
        speed=0.6,
    )

    app = CrapsApp(
        game_settings=game_settings,
        animation_settings=animation_settings,
    )

    app.run()

if __name__ == "__main__":
    main()