from engine import Game
from simulator import Simulator, PassLineStrategy

game = Game()
player = game.add_player()

strategy = PassLineStrategy(player)
simulator = Simulator(game, strategy)

simulator.run(1000)

print(f"Rolls: {simulator.roll_count}")
print(f"Final bankroll: ${player.bankroll}")