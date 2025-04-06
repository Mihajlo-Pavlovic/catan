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

def test_slash_correct_amount(player):
    """Test slashing correct amount of resources."""
    # Give player 10 resources
    player.resources = {
        "wood": 3,
        "brick": 2,
        "sheep": 2,
        "wheat": 2,
        "ore": 1
    }  # Total: 10 resources, should slash 5
    
    # Slash half of resources
    player.slash({
        "wood": 2,
        "brick": 1,
        "sheep": 1,
        "wheat": 1
    })  # Slashing 5 resources
    
    # Verify remaining resources
    assert player.resources == {
        "wood": 1,
        "brick": 1,
        "sheep": 1,
        "wheat": 1,
        "ore": 1
    }

def test_slash_insufficient_total(player):
    """Test slashing fails when total resources are 7 or fewer."""
    # Give player 7 resources
    player.resources = {
        "wood": 2,
        "brick": 1,
        "sheep": 1,
        "wheat": 2,
        "ore": 1
    }  # Total: 7 resources
    
    with pytest.raises(AssertionError, match="Cannot slash if player has 7 or fewer resources"):
        player.slash({"wood": 1, "brick": 1})

def test_slash_wrong_amount(player):
    """Test slashing fails when discarding wrong amount."""
    # Give player 10 resources
    player.resources = {
        "wood": 3,
        "brick": 2,
        "sheep": 2,
        "wheat": 2,
        "ore": 1
    }  # Total: 10 resources, should slash 5
    
    # Try to slash wrong amount
    with pytest.raises(AssertionError, match="Must discard exactly 5 cards"):
        player.slash({"wood": 2, "brick": 1})  # Only slashing 3 resources

def test_slash_invalid_resource(player):
    """Test slashing fails with invalid resource type."""
    # Give player 8 resources
    player.resources = {
        "wood": 4,
        "brick": 2,
        "sheep": 2
    }
    
    with pytest.raises(AssertionError, match="Invalid resource type"):
        player.slash({"invalid_resource": 4})

def test_slash_insufficient_specific_resource(player):
    """Test slashing fails when trying to slash more of a resource than available."""
    # Give player 8 resources
    player.resources = {
        "wood": 4,
        "brick": 2,
        "sheep": 2
    }
    
    with pytest.raises(AssertionError, match="Not enough wood"):
        player.slash({"wood": 5})  # Trying to slash 5 wood when only 4 available

def test_slash_negative_amount(player):
    """Test slashing fails when trying to slash negative amount."""
    # Give player 8 resources
    player.resources = {
        "wood": 4,
        "brick": 2,
        "sheep": 2
    }
    
    with pytest.raises(AssertionError, match="Cannot slash negative amount"):
        player.slash({"wood": -1})

def test_slash_odd_number_resources(player):
    """Test slashing with odd number of total resources."""
    # Give player 9 resources
    player.resources = {
        "wood": 3,
        "brick": 2,
        "sheep": 2,
        "wheat": 1,
        "ore": 1
    }  # Total: 9 resources, should slash 4
    
    # Slash half (rounded down)
    player.slash({
        "wood": 2,
        "brick": 1,
        "sheep": 1
    })  # Slashing 4 resources
    
    # Verify remaining resources
    assert player.resources == {
        "wood": 1,
        "brick": 1,
        "sheep": 1,
        "wheat": 1,
        "ore": 1
    }

def test_slash_multiple_combinations(player):
    """Test different valid combinations of resource slashing."""
    # Give player 8 resources
    player.resources = {
        "wood": 3,
        "brick": 2,
        "sheep": 3
    }  # Total: 8 resources, should slash 4
    
    # Try first valid combination
    player_resources = player.resources.copy()
    player.slash({"wood": 2, "brick": 1, "sheep": 1})
    assert sum(player.resources.values()) == sum(player_resources.values()) - 4
    
    # Reset and try different valid combination
    player.resources = player_resources
    player.slash({"wood": 1, "brick": 2, "sheep": 1})
    assert sum(player.resources.values()) == sum(player_resources.values()) - 4 