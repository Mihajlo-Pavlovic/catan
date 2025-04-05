import pytest
from game.constants import VERTEX_NEIGHBORS

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