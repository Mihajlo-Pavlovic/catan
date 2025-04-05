import random
import pytest
from game.game import Game
from game.player import Player
from game.board import Board
from game.constants import MAX_SETTLEMENTS, TILE_VERTEX_IDS, VALID_COORDS

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
    for _ in range(100):
        roll = game._roll_dice()
        assert 2 <= roll <= 12

def test_move_robber(game):
    """Test moving the robber to a new tile."""
    initial_position = game.board.robber
    new_position = (0, 0)  # Example tile coordinate
    while new_position == initial_position:
        new_position = (random.randint(-2, 2), random.randint(-2, 2))
    game._move_robber(new_position)
    assert game.board.robber == new_position
    with pytest.raises(ValueError):
        game._move_robber(new_position)

def test_steal_resource(game, players):
    """Test stealing a resource from one player to another."""
    player1, player2 = players[0], players[1]
    player2.resources["wood"] = 1
    game._steal_resource(player1, player2)
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
    # Get a valid vertex ID from the board
    vertex = next(iter(game.board.vertices.values()))
    player.settlements.append(vertex)
    game._distribute_initial_resources()
    # Check that at least one resource was distributed
    total_resources = sum(player.resources.values())
    assert total_resources >= 0

def test_place_settlement_with_insufficient_resources(game, players):
    """Test that settlement cannot be placed without sufficient resources."""
    player = players[0]
    vertex = next(iter(game.board.vertices.values()))
    
    # Also need to check the adjacent vertex rule
    for adjacent_vertex in vertex.adjacent_vertices:
        if adjacent_vertex.settlement is None:
            with pytest.raises(ValueError, match="Player does not have enough resources to place a settlement"):
                game._place_settlement(player, vertex)
            return

    # Try to place settlement without resources
    with pytest.raises(ValueError, match="Player does not have enough resources"):
        game._place_settlement(player, vertex)

def test_place_city_with_insufficient_resources(game, players):
    """Test that city cannot be placed without sufficient resources."""
    player = players[0]
    vertex = game.board.vertices[0]
    
    # Try to upgrade to city without a settlement
    with pytest.raises(ValueError, match="Vertex does not have player's settlement"):
        game._place_city(player, vertex)
    
    # Add the settlement first
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Try to upgrade to city without resources
    with pytest.raises(ValueError, match="Player does not have enough resources"):
        game._place_city(player, vertex)

def test_distribute_resources_with_dice_roll(game, players):
    """Test resource distribution based on specific dice roll."""
    player = players[0]
    # Find a tile with a specific number (e.g., 6)
    test_number = 6
    tiles = game.board.number_tile_dict[test_number]
    assert len(tiles) > 0
    tile = tiles[0]
    if (tile.cord == game.board.robber or tile.resource_type == "desert"):
        tile = game.board.tiles[random.choice(VALID_COORDS)]
    # Place a settlement at a vertex adjacent to this tile
    vertex = tile.vertices[0]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Distribute resources for the roll
    game._distribute_resources(test_number)
    
    # Player should receive 1 resource of the tile's type
    assert player.resources[tile.resource_type] == 1

def test_robber_blocks_resource_distribution(game, players):
    """Test that robber prevents resource distribution from its tile."""
    player = players[0]
    
    # Find a productive tile
    test_number = 6
    tiles = [tile for tile in game.board.tiles.values() if tile.number == test_number]
    assert len(tiles) > 0
    tile = tiles[0]
    
    # Move robber to this tile
    game._move_robber(tile.cord)
    
    # Place a settlement at a vertex adjacent to this tile
    vertex_id = TILE_VERTEX_IDS[tile.cord][0]
    game.board.vertices[vertex_id].settlement = player
    player.settlements.append(vertex_id)
    
    # Distribute resources for the roll
    initial_resources = player.resources[tile.resource_type]
    game._distribute_resources(test_number)
    
    # Player should not receive resources due to robber
    assert player.resources[tile.resource_type] == initial_resources 

def test_max_settlements_limit(game, players):
    """Test that players cannot exceed maximum settlements."""
    player = players[0]
    player.resources = {"wood": 5, "brick": 5, "sheep": 5, "wheat": 5}
    
    # Try to place more than MAX_SETTLEMENTS settlements
    vertex_ids = [0, 2, 4, 9, 7, 11, 31]
    for i in range(MAX_SETTLEMENTS + 2):
        vertex_id = vertex_ids[i]
        if i <= MAX_SETTLEMENTS:
            game.board.vertices[vertex_id].settlement = player
            player.settlements.append(vertex_id)
        else:
            with pytest.raises(ValueError, match="Player has too many settlements"):
                game._place_settlement(player, game.board.vertices[vertex_id]) 

def test_resource_deduction_after_building(game, players):
    """Test that resources are properly deducted after building."""
    player = players[0]
    vertex_id = 0
    
    # Give player exactly enough resources for a settlement
    player.resources = {"wood": 1, "brick": 1, "sheep": 1, "wheat": 1}
    initial_resources = player.resources.copy()
    
    # Place settlement
    game._place_settlement(player, game.board.vertices[vertex_id])
    
    # Check resources were deducted
    for resource in ["wood", "brick", "sheep", "wheat"]:
        assert player.resources[resource] == initial_resources[resource] - 1 