from ui import CrapsApp
from engine import GameSettings, VigSetting

def main():
    settings = GameSettings(
        buy_vig_setting=VigSetting.AUTO_BUY
    )
    app = CrapsApp(settings=settings)
    app.run()

if __name__ == "__main__":
    main()