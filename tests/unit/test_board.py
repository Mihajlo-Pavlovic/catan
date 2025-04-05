import pytest
from game.board import Board, Vertex, Edge, Tile
from game.constants import (
    MAX_VERTEX_ID,
    VERTEX_NEIGHBORS, 
    TILE_VERTEX_IDS, 
    VALID_COORDS, 
    RESOURCE_DISTRIBUTION,
    NUMBER_TOKENS
)

# Fixtures
@pytest.fixture
def board():
    """Create a fresh board instance for each test."""
    return Board()

@pytest.fixture
def vertex():
    """Create a vertex instance for testing."""
    return Vertex(0)

@pytest.fixture
def edge():
    """Create an edge instance for testing."""
    return Edge(0, 1)

@pytest.fixture
def tile():
    """Create a tile instance for testing."""
    return Tile("wood", (0, 0))

# Vertex Tests
class TestVertex:
    def test_vertex_initialization(self, vertex):
        """Test vertex is properly initialized."""
        assert vertex.id == 0
        assert vertex.settlement is None
        assert vertex.city is None
        assert vertex.adjacent_tiles == []
        assert vertex.adjacent_vertices == []

# Edge Tests
class TestEdge:
    def test_edge_initialization(self, edge):
        """Test edge is properly initialized."""
        assert edge.vertices == (0, 1)
        assert edge.road is None

# Tile Tests
class TestTile:
    def test_tile_initialization(self, tile):
        """Test tile is properly initialized."""
        assert tile.resource_type == "wood"
        assert tile.cord == (0, 0)
        assert tile.number is None
        assert tile.vertex_ids == []

    def test_tile_string_representation(self, tile):
        """Test tile string representation."""
        tile.number = 6
        assert str(tile) == "wood 6"

# Board Tests
class TestBoard:
    def test_board_initialization(self, board):
        """Test board is properly initialized."""
        assert isinstance(board.tiles, dict)
        assert isinstance(board.vertices, dict)
        assert isinstance(board.edges, dict)
        assert isinstance(board.number_tile_dict, dict)
        assert board.robber is not None

    def test_tile_generation(self, board):
        """Test tiles are properly generated."""
        # Check correct number of tiles
        assert len(board.tiles) == len(VALID_COORDS)
        
        # Check resource distribution
        resource_count = {}
        for tile in board.tiles.values():
            resource_count[tile.resource_type] = resource_count.get(tile.resource_type, 0) + 1
        
        assert resource_count == RESOURCE_DISTRIBUTION

    def test_vertex_generation(self, board):
        """Test vertices are properly generated."""
        # Check all vertices exist

        max_vertex_id = max(VERTEX_NEIGHBORS.keys())
        assert max_vertex_id == MAX_VERTEX_ID
        assert len(board.vertices) == max_vertex_id + 1
        
        # Check vertex connections
        for vertex_id, vertex in board.vertices.items():
            expected_neighbors = VERTEX_NEIGHBORS[vertex_id]
            actual_neighbors = [v.id for v in vertex.adjacent_vertices]
            assert sorted(actual_neighbors) == sorted(expected_neighbors)

    def test_number_token_distribution(self, board):
        """Test number tokens are properly distributed."""
        # Count number tokens
        number_counts = {}
        for tile in board.tiles.values():
            if tile.number is not None:
                number_counts[tile.number] = number_counts.get(tile.number, 0) + 1
        
        # Check all numbers from NUMBER_TOKENS are used
        for number in NUMBER_TOKENS:
            assert number in board.number_tile_dict

    def test_robber_initial_placement(self, board):
        """Test robber is initially placed on desert tile."""
        robber_tile = board.tiles[board.robber]
        assert robber_tile.resource_type == "desert"

    def test_vertex_tile_connections(self, board):
        """Test vertices are properly connected to tiles."""
        for coord, tile in board.tiles.items():
            vertex_ids = TILE_VERTEX_IDS[coord]
            # Check tile's vertices
            assert len(tile.vertex_ids) == len(vertex_ids)
            # Check vertices' tiles
            for vertex_id in vertex_ids:
                vertex = board.vertices[vertex_id]
                assert coord in [t.cord for t in vertex.adjacent_tiles]

    def test_get_edge(self, board):
        """Test edge retrieval."""
        # Test existing edge
        edge = board.get_edge(0, 1)
        assert isinstance(edge, Edge)
        assert edge.vertices == (0, 1)

        # Test non-existing edge
        with pytest.raises(KeyError):
            board.get_edge(0, 99)

def test_vertex_neighbor_relationships():
    """
    Test that all vertex neighbor relationships are bidirectional.
    For each vertex and its neighbors, verify that the vertex is also 
    in each neighbor's neighbor list.
    """
    for vertex, neighbors in VERTEX_NEIGHBORS.items():
        # Check each neighbor of the current vertex
        for neighbor in neighbors:
            # Verify that the neighbor exists in VERTEX_NEIGHBORS
            assert neighbor in VERTEX_NEIGHBORS, f"Vertex {neighbor} is listed as a neighbor but doesn't exist in VERTEX_NEIGHBORS"
            
            # Verify that the current vertex is in the neighbor's neighbor list
            assert vertex in VERTEX_NEIGHBORS[neighbor], \
                f"Vertex {vertex} is a neighbor of {neighbor}, but {neighbor} is not a neighbor of {vertex}"
            
            # Verify that both vertices have each other in their neighbor lists
            assert neighbor in VERTEX_NEIGHBORS[vertex] and vertex in VERTEX_NEIGHBORS[neighbor], \
                f"Inconsistent neighbor relationship between vertices {vertex} and {neighbor}"

def test_vertex_neighbor_count():
    """
    Test that each vertex has 2 or 3 neighbors (valid for Catan board).
    """
    for vertex, neighbors in VERTEX_NEIGHBORS.items():
        assert 2 <= len(neighbors) <= 3, \
            f"Vertex {vertex} has {len(neighbors)} neighbors, expected 2 or 3 neighbors"

def test_edges_are_bidirectional():
    """
    Test that all vertex connections are bidirectional.
    If vertex A has vertex B as a neighbor, then vertex B must have vertex A as a neighbor.
    """
    for vertex, neighbors in VERTEX_NEIGHBORS.items():
        for neighbor in neighbors:
            # Check if the neighbor has this vertex in its neighbor list
            assert vertex in VERTEX_NEIGHBORS[neighbor], \
                f"Edge not bidirectional: {vertex} has {neighbor} as neighbor, but {neighbor} doesn't have {vertex}"

def test_edge_creation_is_consistent():
    """
    Test that edge IDs are consistent regardless of direction.
    Edge (1,2) should be the same as edge (2,1).
    """
    from game.board import Board
    board = Board()
    
    # Check a few sample edges
    test_pairs = [
        (0, 1),
        (2, 3),
        (4, 5)
    ]
    
    for v1, v2 in test_pairs:
        # Both orderings should give the same edge
        edge1 = tuple(sorted((v1, v2)))
        edge2 = tuple(sorted((v2, v1)))
        
        assert edge1 in board.edges
        assert edge1 == edge2, f"Edge ordering inconsistent: {edge1} != {edge2}"
        assert board.edges[edge1] == board.edges[edge2], \
            f"Different edge objects for same connection: {edge1} and {edge2}"

def test_number_tile_mapping(board):
    """Test that number_tile_dict correctly maps numbers to tiles."""
    for number, tile in board.number_tile_dict.items():
        assert 2 <= number <= 12
        assert tile.number == number
        assert tile.resource_type != "desert"

def test_vertex_tile_connections(board):
    """Test that vertices are correctly connected to adjacent tiles."""
    for tile_coord, tile_vertex_ids in TILE_VERTEX_IDS.items():
        tile = board.tiles[tile_coord]
        for vertex_id in tile_vertex_ids:
            vertex = board.vertices[vertex_id]
            assert tile in vertex.adjacent_tiles 