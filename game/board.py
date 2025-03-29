import random
from game.constants import RESOURCE_DISTRIBUTION, NUMBER_TOKENS, CORDS_UNWRAPED, VALID_COORDS, VERTEX_OFFSETS


Vertex_Id = tuple[int, int, int]
class Vertex:
    """
    Represents a vertex (intersection) on the Catan board.
    
    A vertex is where settlements and cities can be built. Each vertex is connected
    to up to three tiles and up to three other vertices.
    
    Attributes:
        id (tuple): A tuple of (q, r, corner_index) identifying the vertex position
        settlement (Player|None): The player who has built on this vertex, or None
        adjacent_tiles (list): List of adjacent tile coordinates as (q, r) tuples
        adjacent_vertices (list): List of adjacent vertex IDs
    """
    def __init__(self, vertex_id: Vertex_Id):
        """
        Initialize a new vertex.

        Args:
            vertex_id (tuple): A tuple of (q, r, corner_index) identifying the vertex position
        """
        self.id = vertex_id  # Tuple (q, r, corner_index)
        self.settlement = None  # Player who owns it, or None
        self.city = None  # Player who owns it, or None
        self.adjacent_tiles = []  # List of tile (q, r) coordinates
        self.adjacent_vertices = []  # Neighboring vertex IDs

Edge_Id = tuple[Vertex_Id, Vertex_Id]
class Edge:
    """
    Represents an edge between two vertices on the Catan board.
    
    An edge is where roads can be built. Each edge connects exactly two vertices.
    
    Attributes:
        vertices (tuple): A tuple of two vertex IDs that this edge connects
        road (Player|None): The player who has built a road on this edge, or None
    """
    def __init__(self, v1_id: Vertex_Id, v2_id: Vertex_Id):
        """
        Initialize a new edge.

        Args:
            v1_id (tuple): ID of the first vertex
            v2_id (tuple): ID of the second vertex
        """
        self.vertices = Edge_Id(v1_id, v2_id)
        self.road = None


class Tile:
    """
    Represents a hexagonal tile on the Catan board.
    
    Each tile has a resource type, coordinates, and a number token (except desert).
    
    Attributes:
        resource_type (str): The type of resource this tile produces
        cord (tuple): The (q, r) coordinates of the tile in the hexagonal grid
        number (int|None): The number token on this tile, or None for desert
    """
    def __init__(self, resource_type, cord):
        """
        Initialize a new tile.

        Args:
            resource_type (str): The type of resource this tile produces
            cord (tuple): The (q, r) coordinates of the tile
        """
        self.resource_type = resource_type
        self.cord = cord
        self.number = None

    def __str__(self):
        """
        Returns a string representation of the tile.

        Returns:
            str: A string showing the resource type and number token
        """
        return f"{self.resource_type} {self.number}"


class Board:
    """
    Represents the Catan game board.
    
    The board consists of hexagonal tiles arranged in a larger hexagon,
    with vertices where settlements/cities can be built and edges where
    roads can be built.
    
    Attributes:
        tiles (list[Tile]): List of all tiles on the board
        vertices (dict): Dictionary mapping vertex IDs to Vertex objects
        edges (dict): Dictionary mapping edge IDs to Edge objects
        nuber_tile_dict (dict): Dictionary mapping number tokens to tiles
    """
    def __init__(self):
        """Initialize a new Catan board with randomly distributed resources and numbers."""
        self.tiles: list[Tile] = []
        self.vertices: dict[Vertex_Id, Vertex] = {}
        self.edges: dict[Edge_Id, Edge] = {}
        self.nuber_tile_dict: dict[int, Tile] = {}
        self.robber: Tile = None

        self._generate_tiles()
        self._generate_vertices()
        self._generate_edges()

    def _generate_tiles(self):
        """
        Generate and place all tiles on the board.
        
        Distributes resources randomly according to the standard game distribution
        and assigns number tokens to all non-desert tiles.
        """
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
                self.robber = tile.cord
            else:
                tile.number = NUMBER_TOKENS[index - desert_passed]
                self.number_tile_dict[tile.number] = tile
    def _generate_vertices(self):
        """
        Generate all vertices on the board.
        
        Creates vertices at each corner of each tile and establishes
        connections between vertices and their adjacent tiles.
        """
        for tile in self.tiles:
            q, r = tile.cord
            for corner in range(6):
                vid = self._get_vertex_id(q, r, corner)
                if vid not in self.vertices:
                    self.vertices[vid] = Vertex(vid)
                self.vertices[vid].adjacent_tiles.append((q, r))

    def _generate_edges(self):
        """
        Generate all edges on the board.
        
        Creates edges between adjacent vertices and establishes
        connections between vertices through these edges.
        """
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
        """
        Calculate the ID of a vertex at a specific corner of a tile.

        Args:
            q (int): Q-coordinate of the tile
            r (int): R-coordinate of the tile
            corner (int): Corner index (0-5) of the tile

        Returns:
            tuple: A tuple (q, r, corner) identifying the vertex
        """
        dq, dr, new_corner = VERTEX_OFFSETS[corner]
        return (q + dq, r + dr, new_corner)

    def display(self):
        """
        Display the board in a simple text-based hexagonal layout.
        
        Prints the board with proper indentation to create a hexagonal shape,
        showing each tile's resource type and number.
        """
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
        """
        Display a detailed view of the board showing tiles and their surrounding vertices.
        
        Prints each tile with its resource type, number token, and the IDs of its
        six surrounding vertices in a visual representation.
        """
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