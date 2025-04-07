import random
from game.constants import DICE_ROLL_PROBABILITIES, MAX_VERTEX_ID, RESOURCE_DISTRIBUTION, NUMBER_TOKENS, CORDS_UNWRAPED, TILE_VERTEX_IDS, VALID_COORDS, VERTEX_NEIGHBORS

Cord = tuple[int, int]
Vertex_Id = int
class Vertex:
    """
    Represents a vertex (intersection) on the Catan board.
    
    A vertex is where settlements and cities can be built. Each vertex is connected
    to up to three tiles and up to three other vertices.
    
    Attributes:
        id (int): vertex id
        settlement (Player|None): The player who has built on this vertex, or None
        adjacent_tiles (list): List of adjacent tile references
        adjacent_vertices (list): List of adjacent vertex references
    """
    def __init__(self, vertex_id: Vertex_Id):
        """
        Initialize a new vertex.

        Args:
            vertex_id (int): vertex id
        """
        self.id = vertex_id  # int
        self.settlement = None  # Player who owns it, or None
        self.city = None  # Player who owns it, or None
        self.adjacent_tiles = []  # List of tile references
        self.adjacent_vertices = []  # Neighboring vertex references
        self.probability_score = 0

    def __str__(self) -> str:
        """
        Returns a string representation of the vertex.

        Returns:
            str: A string showing the vertex id
        """
        return f"Vertex({self.id})"

Edge_Id = tuple[Vertex_Id, Vertex_Id]
class Edge:
    """
    Represents an edge between two vertices on the Catan board.
    
    An edge is where roads can be built. Each edge connects exactly two vertices.
    
    Attributes:
        vertices (tuple[Vertex_Id, Vertex_Id]): A tuple of two vertex IDs that this edge connects
        road (Player|None): The player who has built a road on this edge, or None
    """
    def __init__(self, v1_id: Vertex_Id, v2_id: Vertex_Id):
        """
        Initialize a new edge.

        Args:
            v1_id (Vertex_Id): ID of the first vertex
            v2_id (Vertex_Id): ID of the second vertex
        """
        self.vertices = (v1_id, v2_id)  # Create a tuple directly
        self.road = None

    def __str__(self) -> str:
        """
        Returns a string representation of the edge.

        Returns:
            str: A string showing the two vertices connected by the edge
        """
        return f"Edge({self.vertices[0]}, {self.vertices[1]})"
    

class Tile:
    """
    Represents a hexagonal tile on the Catan board.
    
    Each tile has a resource type, coordinates, and a number token (except desert).
    
    Attributes:
        resource_type (str): The type of resource this tile produces
        cord (tuple): The (q, r) coordinates of the tile in the hexagonal grid
        number (int|None): The number token on this tile, or None for desert
    """
    def __init__(self, resource_type: str, cord: Cord):
        """
        Initialize a new tile.

        Args:
            resource_type (str): The type of resource this tile produces
            cord (tuple): The (q, r) coordinates of the tile
        """
        self.resource_type = resource_type
        self.cord = cord
        self.number = None
        self.vertices = []
    def __str__(self) -> str:
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
        tiles (dict[Cord, Tile]): Dictionary mapping tile coordinates to Tile objects
        vertices (dict[Vertex_Id, Vertex]): Dictionary mapping vertex IDs to Vertex objects
        edges (dict[Edge_Id, Edge]): Dictionary mapping edge IDs to Edge objects
        number_tile_dict (dict[int, list[Tile]]): Dictionary mapping dice numbers to lists of tiles
        robber (Cord): Coordinates of the tile where the robber is located
    """
    def __init__(self):
        """Initialize a new Catan board with randomly distributed resources and numbers."""
        self.tiles: dict[Cord, Tile] = {}
        self.vertices: dict[Vertex_Id, Vertex] = {}
        self.edges: dict[Edge_Id, Edge] = {}
        self.number_tile_dict: dict[int, list[Tile]] = {i: [] for i in NUMBER_TOKENS}
        self.robber: Cord = None

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
            self.tiles[coord] = Tile(res, coord)

        # Assign number tokens
        desert_passed = 0
        for index, coord in enumerate(CORDS_UNWRAPED):
            tile = self.tiles[coord]
            if tile.resource_type == "desert":
                desert_passed += 1
                self.robber = coord
            else:
                tile.number = NUMBER_TOKENS[index - desert_passed]
                self.number_tile_dict[tile.number].append(tile)

            

    def _generate_vertices(self) -> None:
        """
        Generate all vertices and establish their connections on the board.
        
        This method:
        1. Creates all vertex objects with unique IDs
        2. Establishes connections between adjacent vertices using VERTEX_NEIGHBORS
        3. Links vertices to their adjacent tiles using TILE_VERTEX_IDS
        
        The method builds the complete vertex network that represents all possible
        building locations on the Catan board. Each vertex knows:
        - Its unique ID
        - Which vertices it connects to (for road placement)
        - Which tiles it touches (for resource collection)
        """
        # Step 1: Create all vertices with unique IDs
        for i in range(MAX_VERTEX_ID + 1):
            vertex = Vertex(i)
            self.vertices[i] = vertex

        # Step 2: Establish vertex-to-vertex connections (for road placement)
        for i in range(MAX_VERTEX_ID + 1):
            for neighbor_id in VERTEX_NEIGHBORS[i]:
                # Add reference to the actual vertex object (not just the ID)
                self.vertices[i].adjacent_vertices.append(self.vertices[neighbor_id])

        # Step 3: Link vertices to their adjacent tiles (for resource collection)
        for cord, tile in self.tiles.items():
            # For each tile, process its six surrounding vertices
            for vertex_id in TILE_VERTEX_IDS[cord]:
                # Add vertex reference to the tile
                tile.vertices.append(self.vertices[vertex_id])
                # Add tile reference to the vertex
                self.vertices[vertex_id].adjacent_tiles.append(tile)
        
        for vertex in self.vertices.values():
            for tile in vertex.adjacent_tiles:
                if tile.number is None:
                    continue
                score = DICE_ROLL_PROBABILITIES[tile.number]
                vertex.probability_score += score

    def _generate_edges(self):
        """
        Generate all valid edges between vertices using VERTEX_NEIGHBORS.
        
        Creates Edge objects for each valid bidirectional connection between vertices,
        ensuring each edge is only created once and can be accessed from either direction.
        """
        # Set to keep track of edges we've already added (in either direction)
        added_edges = set()
        
        # Iterate through all vertices and their neighbors
        for vertex_id, neighbors in VERTEX_NEIGHBORS.items():
            for neighbor_id in neighbors:
                # Create a canonical edge ID (always use smaller vertex ID first)
                v1, v2 = sorted((vertex_id, neighbor_id))
                edge_id = (v1, v2)
                
                # Only add the edge if we haven't seen it before
                if edge_id not in added_edges:
                    self.edges[edge_id] = Edge(v1, v2)
                    added_edges.add(edge_id)
                    
                    # Add the reverse direction to the set to prevent duplicates
                    # reverse_edge_id = (v2, v1)
                    # added_edges.add(reverse_edge_id)

    def get_edge(self, v1: int, v2: int) -> Edge:
        """
        Get the edge between two vertices, regardless of order.
        
        Args:
            v1 (int): First vertex ID
            v2 (int): Second vertex ID
            
        Returns:
            Edge: The edge connecting the two vertices
            
        Raises:
            KeyError: If no edge exists between these vertices
        """
        edge_id = tuple(sorted((v1, v2)))
        return self.edges[edge_id]

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
    
    def display_board(self):
        """
        Display a detailed view of the board showing tiles and their surrounding vertices.

        Prints each tile with its resource type, number token, and the IDs of its
        six surrounding vertices in a visual representation.
        """
        print("\n🗺️  Board Layout (Tiles + Surrounding Vertices):")

        for tile in self.tiles.values():
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