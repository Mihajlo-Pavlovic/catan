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