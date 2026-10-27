
from engine import (
    Game,
    GameSettings,
    Wager,
    WagerType,
    VigSetting,
    defs,
)


def test_place_buy_place_conversion():
    game = Game(
        settings=GameSettings(
            buy_vig_setting=VigSetting.UP_FRONT,
        )
    )

    player = game.add_player()

    wager = Wager(
        definition=defs.PLACE_BET,
        player=player,
        game=game,
        value=100,
        target=4,
    )

    game.place_wager(wager)

    original_id = wager.id

    assert wager.is_buy is False
    assert wager.collected_vig == 0
    assert player.bankroll == 1400

    # Convert Place to Buy.
    game.set_wager_buy_status(wager, True)

    assert wager.is_buy is True
    assert wager.collected_vig == 5
    assert player.bankroll == 1395

    # Convert Buy back to Place.
    game.set_wager_buy_status(wager, False)

    assert wager.is_buy is False
    assert wager.collected_vig == 0
    assert player.bankroll == 1400

    # Original wager is preserved.
    assert wager in game.wagers
    assert wager.id == original_id
    assert wager.value == 100
    assert wager.target == 4
    assert game.get_wager(
        player,
        WagerType.PLACE_BET,
        target=4,
    ) is wager
