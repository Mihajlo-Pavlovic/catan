# main.py

from game.player import Player
from game.game_runner import run_game_with_agents
from agent.simple_builder_agent.simple_builder_agent import SimpleAgent

def main():
    # Create players
    player1 = Player(name="Player 1", color="red")
    player2 = Player(name="Player 2", color="blue")
    player3 = Player(name="Player 3", color="green")
    
    print("🎮 Starting Catan game simulation...")
    print(f"Players: {player1.name} ({player1.color}), {player2.name} ({player2.color}), {player3.name} ({player3.color})")
    
    # Run the game using the game runner
    run_game_with_agents()

if __name__ == "__main__":
    main()