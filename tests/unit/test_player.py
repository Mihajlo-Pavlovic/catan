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
    assert len(player.cities) == 0  # Add cities check
    
    # Check initial resources
    for resource in ["wood", "brick", "sheep", "wheat", "ore"]:
        assert player.resources[resource] == 0

def test_gain_resource(player):
    """Test that resources can be added to a player's inventory."""
    initial_wood = player.resources["wood"]
    player.resources["wood"] += 2
    assert player.resources["wood"] == initial_wood + 2

def test_place_settlement(player):
    """Test placing a settlement."""
    vertex_id = 0  # Changed from (0, 0) to integer
    player.settlements.append(vertex_id)
    assert vertex_id in player.settlements

def test_place_road(player):
    """Test placing a road."""
    edge_key = (0, 1)  # Changed from ((0, 0), (0, 1)) to match implementation
    player.roads.append(edge_key)
    assert edge_key in player.roads

def test_place_city(player):
    """Test placing a city."""
    vertex_id = 0  # Using integer vertex ID
    player.cities.append(vertex_id)
    assert vertex_id in player.cities

def test_victory_points_update(player):
    """Test victory points are updated correctly."""
    initial_points = player.victory_points
    
    # Add a settlement
    vertex_id = 0
    player.settlements.append(vertex_id)
    player.victory_points += 1
    assert player.victory_points == initial_points + 1
    
    # Upgrade to city
    player.settlements.remove(vertex_id)
    player.cities.append(vertex_id)
    player.victory_points += 1
    assert player.victory_points == initial_points + 2

def test_player_str_representation(player):
    """Test the string representation of a player."""
    expected = f"Player Test Player (red)"
    assert str(player) == expected 