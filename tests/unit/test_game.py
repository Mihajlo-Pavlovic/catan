import pytest
from game.game import Game
from game.player import Player
from game.board import Board

@pytest.fixture
def board():
    """Fixture to create a board instance for tests."""
    return Board()

@pytest.fixture
def players():
    """Fixture to create a list of players for tests."""
    return [
        Player("Player 1", "red"),
        Player("Player 2", "blue"),
        Player("Player 3", "green"),
        Player("Player 4", "yellow")
    ]

@pytest.fixture
def game(players):
    """Fixture to create a game instance for tests."""
    return Game(players)

def test_game_initialization(game, players):
    """Test that a game is correctly initialized."""
    assert len(game.players) == 4
    assert isinstance(game.board, Board)
    assert game.players == players

def test_roll_dice(game):
    """Test that dice roll returns valid values."""
    for _ in range(100):  # Test multiple rolls
        roll = game._roll_dice()
        assert 2 <= roll <= 12

def test_move_robber(game):
    """Test moving the robber to a new tile."""
    initial_position = game.board.robber
    new_position = (0, 0)  # Example tile coordinate
    
    # Move robber to new position
    game._move_robber(new_position)
    assert game.board.robber == new_position
    
    # Try to move robber to same position
    with pytest.raises(ValueError):
        game._move_robber(new_position)

def test_steal_resource(game, players):
    """Test stealing a resource from one player to another."""
    player1, player2 = players[0], players[1]
    
    # Give player2 some resources
    player2.resources["wood"] = 1
    
    # Steal resource
    game._steal_resource(player1, player2)
    
    # Check that resource was transferred
    assert player1.resources["wood"] == 1
    assert player2.resources["wood"] == 0

def test_cannot_steal_from_self(game, players):
    """Test that a player cannot steal from themselves."""
    player = players[0]
    with pytest.raises(ValueError):
        game._steal_resource(player, player)

def test_distribute_resources(game, players):
    """Test resource distribution based on dice roll."""
    player = players[0]
    vertex_id = (0, 0, 0)  # Example vertex ID
    
    # Place settlement and give it some resources
    player.place_settlement(vertex_id)
    game._distribute_initial_resources()
    
    # Check that resources were distributed
    total_resources = sum(player.resources.values())
    assert total_resources > 0

def test_place_settlement_with_insufficient_resources(game, players):
    """Test that settlement cannot be placed without sufficient resources."""
    player = players[0]
    vertex_id = (0, 0, 0)  # Example vertex ID
    
    # Try to place settlement without resources
    with pytest.raises(ValueError):
        game._place_settlement(player, vertex_id)

def test_place_city_with_insufficient_resources(game, players):
    """Test that city cannot be placed without sufficient resources."""
    player = players[0]
    vertex_id = (0, 0, 0)  # Example vertex ID
    
    # Place settlement first
    player.place_settlement(vertex_id)
    
    # Try to upgrade to city without resources
    with pytest.raises(ValueError):
        game._place_city(player, vertex_id) 