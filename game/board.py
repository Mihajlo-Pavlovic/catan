import random
from game.constants import RESOURCE_DISTRIBUTION, NUMBER_TOKENS, CORDS_UNWRAPED, VALID_COORDS

class Tile:
    def __init__(self, resource_type, cord):
        self.resource_type = resource_type
        self.cord = cord
        self.number = None

    def __str__(self):
        return f"{self.resource_type} {self.number}"
    
class Board:
    def __init__(self):
        self.tiles: list[Tile] = []
        self._generate_tiles()

    def _generate_tiles(self):
        resources = []
        for resource, count in RESOURCE_DISTRIBUTION.items():
            resources.extend([resource] * count)
        random.shuffle(resources)
        for coord in  VALID_COORDS:
            res = resources.pop()
            self.tiles.append(Tile(res, coord))
        desert_passed = 0
        for index, coord in enumerate(CORDS_UNWRAPED):
            tile = next((t for t in self.tiles if t.cord == coord), None)
            if(tile.resource_type == "desert"):
                desert_passed += 1
            else:
                tile.number = NUMBER_TOKENS[index - desert_passed]

    def display(self):
        print("Catan Board (hex layout):\n")

        layout = [
            (0, 3),
            (3, 7),
            (7, 12),
            (12, 16),
            (16, 19)
        ]

        for start, end in layout:
            row_tiles = self.tiles[start:end]
            padding = "  " * (2 - (start // 3))  # makes the shape "hex"
            row_str = padding + "   ".join(str(tile) for tile in row_tiles)
            print(row_str)

        print()

    