from ui import CrapsApp, AnimationSettings
from engine import GameSettings, VigSetting

def main():
    game_settings = GameSettings(
        buy_vig_setting=VigSetting.AUTO_BUY
    )

    animation_settings = AnimationSettings(
        speed_multiplier=5.0,
    )

    app = CrapsApp(
        game_settings=game_settings,
        animation_settings=animation_settings,
    )

    app.run()

if __name__ == "__main__":
    main()