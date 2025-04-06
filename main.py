# main.py

from game.constants import DICE_ROLL_PROBABILITIES
from game.game import Game
from game.player import Player
from agent.simple_builder_agent import SimpleAgent

def main():
    players = [Player("Player 1", "red"), Player("Player 2", "blue")]
    game = Game(players)
    vertex_probability_score = {}
    for vertex in game.board.vertices.values():
        for tile in vertex.adjacent_tiles:
            if tile.number is None:
                continue
            score = DICE_ROLL_PROBABILITIES[tile.number]
            vertex_probability_score[vertex.id] = score
    print(vertex_probability_score)
    return
    agent = SimpleAgent(players[0])
    agent.decide_turn_actions(game)


if __name__ == "__main__":
    main()