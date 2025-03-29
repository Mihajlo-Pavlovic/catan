import random
from game.constants import RESOURCE_DISTRIBUTION, NUMBER_TOKENS, CORDS_UNWRAPED, VALID_COORDS, VERTEX_OFFSETS


class Vertex:
    def __init__(self, vertex_id):
        self.id = vertex_id  # Tuple (q, r, corner_index)
        self.settlement = None  # Player who owns it, or None
        self.adjacent_tiles = []  # List of tile (q, r) coordinates
        self.adjacent_vertices = []  # Neighboring vertex IDs (optional for road building)


class Edge:
    def __init__(self, v1_id, v2_id):
        self.vertices = (v1_id, v2_id)  # Tuple of vertex IDs
        self.road = None  # Player who built the road, or None




    
class Edge:
    def __init__(self, v1_id, v2_id):
        self.vertices = (v1_id, v2_id)  # Tuple of vertex IDs
        self.road = None  # Player who built the road, or None

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
        self.vertices: dict[tuple[int, int, int], Vertex] = {}
        self._generate_tiles()
        self._generate_vertices()

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

    def _generate_vertices(self):
      self.vertices = {}  # (q, r, corner) → Vertex

      for (q, r), tile in self.tiles.items():
          for corner in range(6):
              vid = self._get_vertex_id(q, r, corner)
              if vid not in self.vertices:
                  self.vertices[vid] = Vertex(vid)
              self.vertices[vid].adjacent_tiles.append((q, r))

    def _get_vertex_id(self, q, r, corner):
        dq, dr, new_corner = VERTEX_OFFSETS[corner]
        return (q + dq, r + dr, new_corner)

    def _generate_edges(self):
        # Connect each vertex to the next in clockwise order
        for (q, r) in self.tiles.keys():
            for i in range(6):
                v1 = self._get_vertex_id(q, r, i)
                v2 = self._get_vertex_id(q, r, (i + 1) % 6)
                edge_key = tuple(sorted([v1, v2]))
                if edge_key not in self.edges:
                    self.edges[edge_key] = Edge(*edge_key)
                    # Optional: connect vertices to each other
                    self.vertices[v1].adjacent_vertices.append(v2)
                    self.vertices[v2].adjacent_vertices.append(v1)


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





    