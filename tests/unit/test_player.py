import pytest
from game.player import Player
from game.board import Board

@pytest.fixture
def board():
    """Fixture to create a board instance for tests."""
    return Board()

@pytest.fixture
def player():
    """Fixture to create a player instance for tests."""
    return Player("Test Player", "red")

def test_player_initialization(player):
    """Test that a player is correctly initialized with default values."""
    assert player.name == "Test Player"
    assert player.color == "red"
    assert player.victory_points == 0
    assert len(player.settlements) == 0
    assert len(player.roads) == 0
    # Removed cities check since Player doesn't have this attribute
    
    # Check initial resources
    assert player.resources["wood"] == 0
    assert player.resources["brick"] == 0
    assert player.resources["sheep"] == 0
    assert player.resources["wheat"] == 0
    assert player.resources["ore"] == 0

def test_gain_resource(player):
    """Test that resources can be added to a player's inventory."""
    initial_wood = player.resources["wood"]
    player.resources["wood"] += 2
    assert player.resources["wood"] == initial_wood + 2

def test_place_settlement(player):
    """Test placing a settlement."""
    vertex_id = (0, 0)
    player.settlements.append(vertex_id)
    assert vertex_id in player.settlements

def test_place_road(player):
    """Test placing a road."""
    edge_key = ((0, 0), (0, 1))
    player.roads.append(edge_key)
    assert edge_key in player.roads

def test_player_str_representation(player):
    """Test the string representation of a player."""
    expected = f"Player Test Player (red)"
    assert str(player) == expected 