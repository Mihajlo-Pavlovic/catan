# game_runner.py
import random
from typing import Dict

from game.game import Game
from game.player import Player

def play_game(game: Game, agents: Dict[Player, "Agent"], max_turns: int = 100):
    """
    Main game loop: cycles through players, rolls dice, distributes resources, 
    and asks each player's agent to decide what to do on their turn.

    Args:
        game (Game): The game instance containing board, players, etc.
        agents (Dict[Player, Agent]): A mapping of Player -> Agent.
            Each Agent is responsible for deciding actions for that Player.
        max_turns (int): Safety limit for the number of turns (avoid infinite games).
    """
    turn_count = 0
    
    # Example: initial resource distribution or any other setup you want.
    # game._distribute_initial_resources()

    while turn_count < max_turns:
        # Check for a winning condition (e.g., first to 10 points).
        for p in game.players:
            if p.victory_points >= 10:
                print(f"Player {p.name} wins with {p.victory_points} points!")
                return
        
        current_player = game.players[turn_count % len(game.players)]
        current_agent = agents[current_player]

        print(f"\n===== Turn {turn_count + 1} - {current_player.name}'s turn =====")

        # 1. Roll dice
        roll = game._roll_dice()
        print(f"🎲 Dice roll: {roll}")

        # 2. If roll == 7, move robber + slash resources
        if roll == 7:
            # (A) Determine which players must discard
            players_to_slash = game._who_to_slash()
            for player in players_to_slash:
                # Here, you could ask an agent to choose which cards to discard:
                # slash_dict = agents[player].choose_cards_to_discard(game)
                # player.slash(slash_dict)

                # For now, let's skip or do something naive:
                pass

            # (B) Current player moves the robber
            # robber_tile = current_agent.choose_robber_tile(game)
            # game._move_robber(robber_tile)

            # (C) Possibly steal one resource from an adjacent settlement
            # victim_player = current_agent.choose_victim(game)
            # game._steal_resource(current_player, victim_player)

        else:
            # Distribute resources based on roll
            game._distribute_resources(roll)

        # 3. Agent decides on building/trading actions
        # Example placeholders:
        # actions = current_agent.decide_turn_actions(game)
        # for action in actions:
        #     game.execute_action(action)

        # 4. End turn logic: pass to next player
        turn_count += 1
    
    # If we reach here, we've hit the max_turns limit
    print("Game ended due to turn limit.")