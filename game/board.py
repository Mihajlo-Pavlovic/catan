import random
from game.constants import RESOURCE_DISTRIBUTION, NUMBER_TOKENS, CORDS_UNWRAPED, VALID_COORDS, VERTEX_OFFSETS


class Vertex:
    def __init__(self, vertex_id):
        self.id = vertex_id  # Tuple (q, r, corner_index)
        self.settlement = None  # Player who owns it, or None
        self.adjacent_tiles = []  # List of tile (q, r) coordinates
        self.adjacent_vertices = []  # Neighboring vertex IDs


class Edge:
    def __init__(self, v1_id, v2_id):
        self.vertices = (v1_id, v2_id)
        self.road = None


class Tile:
    def __init__(self, resource_type, cord):
        self.resource_type = resource_type
        self.cord = cord  # (q, r)
        self.number = None

    def __str__(self):
        return f"{self.resource_type} {self.number}"


class Board:
    def __init__(self):
        self.tiles: list[Tile] = []
        self.vertices: dict[tuple[int, int, int], Vertex] = {}
        self.edges: dict[tuple, Edge] = {}
        self._generate_tiles()
        self._generate_vertices()
        self._generate_edges()

    def _generate_tiles(self):
        resources = []
        for resource, count in RESOURCE_DISTRIBUTION.items():
            resources.extend([resource] * count)
        random.shuffle(resources)

        for coord in VALID_COORDS:
            res = resources.pop()
            self.tiles.append(Tile(res, coord))

        # Assign number tokens
        desert_passed = 0
        for index, coord in enumerate(CORDS_UNWRAPED):
            tile = next((t for t in self.tiles if t.cord == coord), None)
            if tile.resource_type == "desert":
                desert_passed += 1
            else:
                tile.number = NUMBER_TOKENS[index - desert_passed]

    def _generate_vertices(self):
        for tile in self.tiles:
            q, r = tile.cord
            for corner in range(6):
                vid = self._get_vertex_id(q, r, corner)
                if vid not in self.vertices:
                    self.vertices[vid] = Vertex(vid)
                self.vertices[vid].adjacent_tiles.append((q, r))

    def _generate_edges(self):
        for tile in self.tiles:
            q, r = tile.cord
            for i in range(6):
                v1 = self._get_vertex_id(q, r, i)
                v2 = self._get_vertex_id(q, r, (i + 1) % 6)
                edge_key = tuple(sorted([v1, v2]))
                if edge_key not in self.edges:
                    self.edges[edge_key] = Edge(*edge_key)
                    self.vertices[v1].adjacent_vertices.append(v2)
                    self.vertices[v2].adjacent_vertices.append(v1)

    def _get_vertex_id(self, q, r, corner):
        dq, dr, new_corner = VERTEX_OFFSETS[corner]
        return (q + dq, r + dr, new_corner)

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
            padding = "  " * (2 - (start // 3))
            row_str = padding + "   ".join(str(tile) for tile in row_tiles)
            print(row_str)

        print()

    def display_tile_layout_with_vertices(self):
        print("\n🗺️  Board Layout (Tiles + Surrounding Vertices):")

        for tile in self.tiles:
            q, r = tile.cord
            vertex_ids = [self._get_vertex_id(q, r, i) for i in range(6)]
            vertex_labels = [f"{vid}" for vid in vertex_ids]

            res = tile.resource_type.upper()
            num = tile.number if tile.number is not None else "--"

            print(f"\nTile ({q:>2}, {r:>2})")
            print(f"      {vertex_labels[0]} ------- {vertex_labels[1]}")
            print(f"     /                     \\")
            print(f"{vertex_labels[5]}   ({res:^8}, {str(num):^2})   {vertex_labels[2]}")
            print(f"     \\                     /")
            print(f"      {vertex_labels[4]} ------- {vertex_labels[3]}")