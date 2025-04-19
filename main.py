# main.py

import time
from game.player import Player
from game.game_runner import run_game_with_agents
from agent.simple_builder_agent.simple_builder_agent import SimpleAgent

def main():
    
    # Run the game using the game runner
    turn_counts = []
    times = []
    for i in range(100):
        # mesure start time
        start_time = time.time()
        turn_count = run_game_with_agents()
        turn_counts.append(turn_count)
        # mesure end time
        end_time = time.time()
        times.append(end_time - start_time)
        print(f"Time taken: {end_time - start_time} seconds")

    print(f"Average turns: {sum(turn_counts) / len(turn_counts)}")
    print(f"Average time: {sum(times) / len(times)}")
    print(f"Total time: {sum(times)}")

if __name__ == "__main__":
    main()