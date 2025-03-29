# main.py

from game.board import Board

def main():
    board = Board()
    board.display_tile_layout_with_vertices()

if __name__ == "__main__":
    main()