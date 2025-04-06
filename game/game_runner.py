# game_runner.py
import random
from typing import Dict

from game.game import Game
from game.player import Player

# 1) Import your SimpleAgent (adjust import path if necessary)
from agent.simple_builder_agent.simple_builder_agent import SimpleAgent

def run_game_with_agents():
    """
    Creates players, assigns them SimpleAgents, and runs the game until a winner is found 
    or we reach the max turn limit.
    """

    # 2) Create players
    player1 = Player(name="Alice", color="red")
    player2 = Player(name="Bob", color="blue")
    player3 = Player(name="Charlie", color="green")

    players = [player1, player2, player3]

    # 3) Create a game instance
    game = Game(players)

    # 4) Map each player to an agent
    agents = [
        SimpleAgent(player1),
        SimpleAgent(player2),
        SimpleAgent(player3),
    ]

    # 5) Perform initial placements (if you want the agent to do them)
    #    For example, the first/second-turn logic your agent might have:
    # 
    # First round of placements
    print("\n🎯 Initial Placement - First Round")
    for agent in agents:
        print(f"\n👤 {agent.player.name}'s turn for initial placement")
        initial_actions = agent.handle_initial_placement_first_turn(game)
        for action_name, action_data in initial_actions:
            if action_name == "place_settlement":
                game._place_settlement(agent.player, game.board.vertices[action_data], True)
                print(f"🏠 {agent.player.name} placed initial settlement at vertex {action_data}")
            elif action_name == "place_road":
                v1, v2 = sorted((action_data[0], action_data[1]))
                edge_obj = game.board.edges[(v1, v2)]
                game._place_road(agent.player, edge_obj, True)
                print(f"🏗️  {agent.player.name} placed initial road at edge {v1}-{v2}")
    
    print("\n📦 Distributing initial resources...")
    game._distribute_initial_resources()

    # Second round of placements
    print("\n🎯 Initial Placement - Second Round")
    for agent in reversed(agents):
        print(f"\n👤 {agent.player.name}'s turn for second placement")
        initial_actions = agent.handle_initial_placement_second_turn(game)
        for action_name, action_data in initial_actions:
            if action_name == "place_settlement":
                game._place_settlement(agent.player, game.board.vertices[action_data], True)
                print(f"🏠 {agent.player.name} placed initial settlement at vertex {action_data}")
            elif action_name == "place_road":
                v1, v2 = sorted((action_data[0], action_data[1]))
                edge_obj = game.board.edges[(v1, v2)]
                game._place_road(agent.player, edge_obj, True)
                print(f"🏗️  {agent.player.name} placed initial road at edge {v1}-{v2}")

    # 6) Now call the turn-based game loop
    play_game(game, agents, max_turns=100)

def play_game(game: Game, agents: Dict[Player, "SimpleAgent"], max_turns: int = 100000):
    """
    Main game loop: cycles through players, rolls dice, distributes resources, 
    and asks each player's agent to decide what to do on their turn.
    """
    turn_count = 0
    
    while turn_count < 100000:
        # Check for a winning condition (e.g., first to 10 points).
        for p in game.players:
            if p.victory_points >= 10:
                print(f"🏆 Player {p.name} wins with {p.victory_points} points!")
                return
        
        current_agent = agents[turn_count % len(game.players)]
        current_player = current_agent.player
        
        print(f"\n🔄 Turn {turn_count + 1} - {current_player.name}'s turn 🔄")

        # 1. Roll dice
        roll = game._roll_dice()
        print(f"🎲 Dice roll: {roll}")

        # 2. If roll == 7, move robber + slash resources
        if roll == 7:
            # (A) Determine which players must discard
            players_to_slash = game._who_to_slash()
            print(f"🔪 Players to slash: {players_to_slash}")
            for player in players_to_slash:
                agent = agents[game.players.index(player)]
                print(f"🔪 Agent: {agent.player.name}")
                discard_dict = agent.handle_slash()
                print(f"🔪 Discard dict: {discard_dict} for player {player.name}")
                player.slash(discard_dict)
            # (B) Current player moves the robber
            robber_coord, victim = current_agent.handle_robber_move(game)
            print(f"🥷 Old robber cord: {game.board.robber}, New Robber coord: {robber_coord}, victim: {victim}")
            game._move_robber(robber_coord)
            if victim is not None and sum(victim.resources.values()) > 0:
                game._steal_resource(current_player, victim)

        else:
            # Distribute resources based on roll
            game._distribute_resources(roll)

        # 3. Agent decides on building/trading actions
        actions = current_agent.decide_turn_actions(game)
        for (action_name, data) in actions:
            if action_name == "place_settlement":
                vertex_id = data
                vertex_obj = game.board.vertices[vertex_id]
                try:
                    game._place_settlement(current_player, vertex_obj)
                    print(f"🏠 {current_player.name} built a settlement on vertex {vertex_id}.")
                except ValueError as e:
                    print(f"🚨 Failed to place settlement: {e}")

            elif action_name == "place_road":
                # data is a tuple (v1_id, v2_id)
                v1_id, v2_id = sorted((data[0], data[1]))
                if (v1_id, v2_id) not in game.board.edges:
                    print(f"🚨 Invalid edge ({v1_id}, {v2_id}).")
                    continue
                edge_obj = game.board.edges[(v1_id, v2_id)]
                try:
                    game._place_road(current_player, edge_obj)
                    print(f"🏗️ {current_player.name} built a road on edge {v1_id}-{v2_id}.")
                except ValueError as e:
                    print(f"🚨 Failed to place road: {e}")

            elif action_name == "place_city":
                vertex_id = data
                vertex_obj = game.board.vertices[vertex_id]
                try:
                    game._place_city(current_player, vertex_obj)
                    print(f"🏙️ {current_player.name} upgraded settlement to a city at vertex {vertex_id}.")
                except ValueError as e:
                    print(f"🚨 Failed to place city: {e}")
            
            else:
                # Unknown action
                print(f"🚨 Unknown action {action_name} requested by agent.")

        # 4. End turn logic: pass to next player
        turn_count += 1

        for p in game.players:
            p.print_status()
    
    # If we reach here, we've hit the max_turns limit
    print(f"Game ended due to turn limit. No winner found. Last turn: {turn_count}")

# (Optional) If you want to run directly from the command line:
if __name__ == "__main__":
    run_game_with_agents()