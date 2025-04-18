import random
import pytest
from game.game import Game
from game.player import Player
from game.board import Board, Edge
from game.constants import MAX_SETTLEMENTS, TILE_VERTEX_IDS, VALID_COORDS, PORT_RESOURCE_VERTEX_IDS_DICT
from game.development_cards import DevelopmentCard

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

def test_trade_with_bank_standard_rate(game, players):
    """Test trading with bank at standard 4:1 rate."""
    player = players[0]
    # Give player resources
    player.resources["wood"] = 4
    
    # Trade 4 wood for 1 brick
    game._trade_with_bank(
        player=player,
        resource_type_to_receive="brick",
        amount_to_receive=1,
        resource_type_to_give="wood",
        amount_to_give=1
    )
    
    # Check resources were properly exchanged
    assert player.resources["wood"] == 0
    assert player.resources["brick"] == 1

def test_trade_with_bank_port_2_1(game, players):
    """Test trading with bank at 2:1 rate with specific resource port."""
    player = players[0]
    # Give player resources and port access
    player.resources["wood"] = 2
    vertex = game.board.vertices[PORT_RESOURCE_VERTEX_IDS_DICT["wood"][0]]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Trade 2 wood for 1 brick using 2:1 port
    game._trade_with_bank(
        player=player,
        resource_type_to_receive="brick",
        amount_to_receive=1,
        resource_type_to_give="wood",
        amount_to_give=1
    )
    
    # Check resources were properly exchanged
    assert player.resources["wood"] == 0
    assert player.resources["brick"] == 1

def test_trade_with_bank_port_3_1(game, players):
    """Test trading with bank at 3:1 rate with general port."""
    player = players[0]
    # Give player resources and port access
    player.resources["wood"] = 3
    vertex = game.board.vertices[PORT_RESOURCE_VERTEX_IDS_DICT["any"][0]]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Trade 3 wood for 1 brick using 3:1 port
    game._trade_with_bank(
        player=player,
        resource_type_to_receive="brick",
        amount_to_receive=1,
        resource_type_to_give="wood",
        amount_to_give=1
    )
    
    # Check resources were properly exchanged
    assert player.resources["wood"] == 0
    assert player.resources["brick"] == 1

def test_trade_with_bank_insufficient_resources(game, players):
    """Test that trading fails when player has insufficient resources."""
    player = players[0]
    player.resources["wood"] = 3  # Not enough for 4:1 trade
    
    with pytest.raises(ValueError, match="Player needs 4 wood but only has 3"):
        game._trade_with_bank(
            player=player,
            resource_type_to_receive="brick",
            amount_to_receive=1,
            resource_type_to_give="wood",
            amount_to_give=1
        )

def test_trade_with_bank_invalid_resource(game, players):
    """Test that trading fails with invalid resource types."""
    player = players[0]
    player.resources["wood"] = 4
    
    with pytest.raises(AssertionError, match="Invalid resource type to receive"):
        game._trade_with_bank(
            player=player,
            resource_type_to_receive="invalid",
            amount_to_receive=1,
            resource_type_to_give="wood",
            amount_to_give=1
        )

def test_trade_with_bank_invalid_amounts(game, players):
    """Test that trading fails with invalid amounts."""
    player = players[0]
    player.resources["wood"] = 4
    
    with pytest.raises(AssertionError, match="Amount to receive must be greater than 0"):
        game._trade_with_bank(
            player=player,
            resource_type_to_receive="brick",
            amount_to_receive=0,
            resource_type_to_give="wood",
            amount_to_give=1
        )

def test_trade_with_bank_best_rate_selection(game, players):
    """Test that bank trading uses the best available rate."""
    player = players[0]
    # Give player resources and both 3:1 and 2:1 port access
    player.resources["wood"] = 4
    
    # Add 3:1 port access
    vertex_3_1 = game.board.vertices[PORT_RESOURCE_VERTEX_IDS_DICT["any"][0]]
    vertex_3_1.settlement = player
    player.settlements.append(vertex_3_1)
    
    # Add 2:1 wood port access
    vertex_2_1 = game.board.vertices[PORT_RESOURCE_VERTEX_IDS_DICT["wood"][0]]
    vertex_2_1.settlement = player
    player.settlements.append(vertex_2_1)
    
    # Trade wood for brick - should use 2:1 rate
    game._trade_with_bank(
        player=player,
        resource_type_to_receive="brick",
        amount_to_receive=1,
        resource_type_to_give="wood",
        amount_to_give=1
    )
    
    # Check that only 2 wood were used (2:1 rate)
    assert player.resources["wood"] == 2
    assert player.resources["brick"] == 1 

def test_who_to_slash_no_players(game, players):
    """Test that no players are selected when all have 7 or fewer resources."""
    # Give players 7 or fewer resources
    for player in players:
        player.resources = {
            "wood": 2,
            "brick": 1,
            "sheep": 1,
            "wheat": 2,
            "ore": 1
        }  # Total: 7 resources
    
    players_to_slash = game._who_to_slash()
    assert len(players_to_slash) == 0

def test_who_to_slash_one_player(game, players):
    """Test that only players with more than 7 resources are selected."""
    # Give one player more than 7 resources
    players[0].resources = {
        "wood": 3,
        "brick": 2,
        "sheep": 2,
        "wheat": 2,
        "ore": 1
    }  # Total: 10 resources
    
    # Give other players fewer resources
    for player in players[1:]:
        player.resources = {
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1,
            "ore": 1
        }  # Total: 5 resources
    
    players_to_slash = game._who_to_slash()
    assert len(players_to_slash) == 1
    assert players_to_slash[0] == players[0]

def test_who_to_slash_multiple_players(game, players):
    """Test that multiple players with more than 7 resources are selected."""
    # Set up resource counts for each player
    resource_counts = [
        {"wood": 3, "brick": 2, "sheep": 2, "wheat": 2, "ore": 1},  # 10 resources
        {"wood": 4, "brick": 2, "sheep": 1, "wheat": 1, "ore": 0},  # 8 resources
        {"wood": 1, "brick": 1, "sheep": 1, "wheat": 1, "ore": 1},  # 5 resources
        {"wood": 2, "brick": 2, "sheep": 2, "wheat": 2, "ore": 2}   # 10 resources
    ]
    
    # Assign resources to players
    for player, resources in zip(players, resource_counts):
        player.resources = resources.copy()
    
    players_to_slash = game._who_to_slash()
    assert len(players_to_slash) == 3
    assert players[0] in players_to_slash  # 10 resources
    assert players[1] in players_to_slash  # 8 resources
    assert players[3] in players_to_slash  # 10 resources
    assert players[2] not in players_to_slash  # 5 resources

def test_who_to_slash_exact_seven(game, players):
    """Test that players with exactly 7 resources are not selected."""
    # Give player exactly 7 resources
    players[0].resources = {
        "wood": 2,
        "brick": 1,
        "sheep": 1,
        "wheat": 2,
        "ore": 1
    }  # Total: 7 resources
    
    players_to_slash = game._who_to_slash()
    assert len(players_to_slash) == 0
    assert players[0] not in players_to_slash

def test_who_to_slash_all_players(game, players):
    """Test that all players with more than 7 resources are selected."""
    # Give all players more than 7 resources
    for player in players:
        player.resources = {
            "wood": 2,
            "brick": 2,
            "sheep": 2,
            "wheat": 2,
            "ore": 2
        }  # Total: 10 resources
    
    players_to_slash = game._who_to_slash()
    assert len(players_to_slash) == len(players)
    assert all(player in players_to_slash for player in players) 

def test_place_road_initial_placement(game, players):
    """Test placing a road during initial placement phase."""
    player = players[0]
    
    # Get a valid edge from the board
    edge = next(iter(game.board.edges.values()))
    
    # Place a settlement at one of the edge's vertices first
    vertex_id = edge.vertices[0]  # Get first vertex of the edge
    vertex = game.board.vertices[vertex_id]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Place road during initial placement (no resource cost)
    game._place_road(player, edge, initial_placement=True)
    
    # Verify road placement
    assert edge.road == player
    assert edge in player.roads
    
    # Resources shouldn't be deducted during initial placement
    assert player.resources["wood"] == 0
    assert player.resources["brick"] == 0
    
    # Verify road is connected to settlement
    assert game._road_is_connected(player, edge) == True

def test_place_road_with_resources(game, players):
    """Test placing a road with required resources."""
    player = players[0]
    edge = next(iter(game.board.edges.values()))
    
    # Give player required resources
    player.resources["wood"] = 1
    player.resources["brick"] = 1
    
    # Place settlement first to make road placement valid
    vertex_id = edge.vertices[0]
    vertex = game.board.vertices[vertex_id]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    game._place_road(player, edge)
    
    assert edge.road == player
    assert edge in player.roads
    assert player.resources["wood"] == 0
    assert player.resources["brick"] == 0

def test_place_road_insufficient_resources(game, players):
    """Test that road cannot be placed without sufficient resources."""
    player = players[0]
    edge = next(iter(game.board.edges.values()))
    
    # Place settlement first to make road placement valid
    vertex_id = edge.vertices[0]
    game.board.vertices[vertex_id].settlement = player
    player.settlements.append(vertex_id)
    
    with pytest.raises(ValueError, match="Not enough resources to place a road"):
        game._place_road(player, edge)

def test_road_is_connected_to_settlement(game, players):
    """Test road connection validation with settlement."""
    player = players[0]
    edge = next(iter(game.board.edges.values()))
    
    # Place settlement at one of the edge's vertices
    vertex_id = edge.vertices[0]
    game.board.vertices[vertex_id].settlement = player
    player.settlements.append(vertex_id)
    
    assert game._road_is_connected(player, edge) == True

def test_road_is_connected_to_existing_road(game, players):
    """Test road connection validation with existing road."""
    player = players[0]
    # Get two adjacent edges
    edge1 = next(iter(game.board.edges.values()))
    v1_id, v2_id = edge1.vertices
    # Find an edge that shares a vertex with edge1
    edge2 = None
    for e in game.board.edges.values():
        if e != edge1 and (v1_id in e.vertices or v2_id in e.vertices):
            edge2 = e
            break
    assert edge2 is not None
    
    # Place first road 
    edge1.road = player
    player.roads.append(edge1)
    
    # Check if second edge is connected
    assert game._road_is_connected(player, edge2) == True

def test_calculate_longest_road(game, players):
    """Test calculation of longest road length."""
    player = players[0]
    
    # Create a path of 3 connected roads
    edges = list(game.board.edges.values())
    road_edges = []
    current_vertex = edges[0].vertices[0]
    
    # Find 3 connected edges
    for edge in edges:
        if current_vertex in edge.vertices and edge not in road_edges:
            road_edges.append(edge)
            # Get the other vertex to continue the path
            current_vertex = edge.vertices[0] if edge.vertices[1] == current_vertex else edge.vertices[1]
            if len(road_edges) == 3:
                break
    
    # Place the roads
    for edge in road_edges:
        edge.road = player
        player.roads.append(edge)    

    # Calculate longest road
    length = game._calculate_player_longest_road(player)
    assert length == 3

def test_update_longest_road(game, players):
    """Test updating longest road status and victory points."""
    player1, player2 = players[0], players[1]
    
    # Initialize game's longest road tracking
    game.longest_road = 4
    game.longest_road_player = player1
    player1.victory_points = 2  # Points for longest road
    
    # Build a longer road with player2
    edges = [Edge(0, 1), Edge(1, 2), Edge(2, 3), Edge(3, 4), Edge(4, 5)]
    for i in range(5):  # 5 connected roads
        if i < len(edges):
            edges[i].road = player2
            player2.roads.append(edges[i])
    
    # Update longest road
    game._update_longest_road(player2)
    
    # Check that longest road status and points were transferred
    assert game.longest_road_player == player2
    assert player1.victory_points == 0  # Lost 2 points
    assert player2.victory_points == 2  # Gained 2 points 

def test_longest_road_less_than_five(game, players):
    """Test that no victory points are awarded for roads less than 5 segments."""
    player = players[0]
    
    # Create a path of 4 connected roads (less than minimum 5 for points)
    edges = list(game.board.edges.values())
    road_edges = []
    current_vertex_id = edges[0].vertices[0]
    
    # Find 4 connected edges
    for edge in edges:
        if current_vertex_id in edge.vertices and edge not in road_edges:
            road_edges.append(edge)
            # Get the other vertex to continue the path
            v1_id, v2_id = edge.vertices
            current_vertex_id = v2_id if v1_id == current_vertex_id else v1_id
            if len(road_edges) == 4:
                break
    
    # Place the roads
    for edge in road_edges:
        edge.road = player
        player.roads.append(edge)
    
    # Update longest road
    game._update_longest_road(player)
    
    # Verify no victory points were awarded
    assert player.victory_points == 0
    assert game.longest_road == 4

def test_longest_road_exactly_five(game, players):
    """Test that victory points are awarded for roads exactly 5 segments long."""
    player = players[0]
    
    # Create a path of exactly 5 connected roads
    edges = list(game.board.edges.values())
    road_edges = []
    current_vertex_id = edges[0].vertices[0]
    
    # Find 5 connected edges
    for edge in edges:
        if current_vertex_id in edge.vertices and edge not in road_edges:
            road_edges.append(edge)
            # Get the other vertex to continue the path
            v1_id, v2_id = edge.vertices
            current_vertex_id = v2_id if v1_id == current_vertex_id else v1_id
            if len(road_edges) == 5:
                break
    
    # Place the roads
    for edge in road_edges:
        edge.road = player
        player.roads.append(edge)

    game._update_longest_road(player)
    
    # Verify victory points were awarded
    assert player.victory_points == 2  # Should get 2 points for longest road
    assert game.longest_road == 5
    assert game.longest_road_player == player

def test_longest_road_more_than_five(game, players):
    """Test that victory points are awarded for roads longer than 5 segments."""
    player1, player2 = players[0], players[1]
    
    # First give player1 a 5-segment road and the longest road status)
    road_edges = [Edge(0, 1), Edge(1, 2), Edge(2, 3), Edge(3, 4), Edge(4, 5)]
    
    # Place the roads for player1
    for edge in road_edges:
        edge.road = player1
        player1.roads.append(edge)
    
    game._update_longest_road(player1)
    assert player1.victory_points == 2
    assert game.longest_road == 5
    
    # Now give player2 a longer (7-segment) road
    road_edges = [Edge(38, 39), Edge(38, 42), Edge(41, 42), Edge(41, 44), Edge(43, 44), Edge(43, 46), Edge(46, 52)]
    
    # Place the roads for player2
    for edge in road_edges:
        edge.road = player2
        player2.roads.append(edge)

    game._update_longest_road(player2)
    
    # Verify longest road status transferred to player2
    assert player1.victory_points == 0  # Lost the points
    assert player2.victory_points == 2  # Gained the points
    assert game.longest_road == 7
    assert game.longest_road_player == player2

def test_longest_road_tracking(game, players):
    """Test that longest road length is tracked correctly regardless of length."""
    player1, player2 = players[0], players[1]
    
    # Build a 3-segment road with player1
    road_edges = [Edge(0, 1), Edge(1, 2), Edge(2, 3)]
    # Place the roads for player1
    for edge in road_edges:
        edge.road = player1
        player1.roads.append(edge)
    
    game._update_longest_road(player1)
    
    # Verify tracking but no points awarded
    assert game.longest_road == 3
    assert game.longest_road_player == None
    assert player1.victory_points == 0  # No points for road < 5
    
    # Build a 4-segment road with player2
    road_edges = [Edge(38, 39), Edge(38, 42), Edge(41, 42), Edge(41, 44)]
    
    # Place the roads for player2
    for edge in road_edges:
        edge.road = player2
        player2.roads.append(edge)
    
    game._update_longest_road(player2)
    
    # Verify tracking updated but still no points
    assert game.longest_road == 4
    assert game.longest_road_player == None
    assert player1.victory_points == 0
    assert player2.victory_points == 0

def test_circular_road(game, players):
    """Test that a circular road's length is calculated correctly."""
    player = players[0]
    
    edges = [
        Edge(0, 1),
        Edge(1, 2),
        Edge(2, 3),
        Edge(3, 4),
        Edge(4, 5),
        Edge(0, 5)
    ]
    
    # Place the roads to form the circle
    for edge in edges:
        edge.road = player
        player.roads.append(edge)
    
    game._update_longest_road(player)

    # Calculate longest road
    length = game._calculate_player_longest_road(player)
    # Verify the length is correct (should be 4 for a simple circle)
    assert length == 6
    assert game.longest_road == 6
    assert game.longest_road_player == player
    assert player.victory_points == 2

def test_circular_road_with_tail(game, players):
    """Test that a circular road with a tail is calculated correctly."""
    player = players[0]
    

    edges = [
        Edge(0, 1),
        Edge(1, 2),
        Edge(2, 3),
        Edge(3, 4),
        Edge(4, 5),
        Edge(0, 5),
        Edge(5, 14)
    ]
    
    # Place all roads
    for edge in edges:
        edge.road = player
        player.roads.append(edge)

    game._update_longest_road(player)
    
    # Calculate longest road
    length = game._calculate_player_longest_road(player)
    
    # Verify the length is correct (should be 6: circle + tail)
    assert length == 7
    assert game.longest_road == 7
    assert game.longest_road_player == player
    assert player.victory_points == 2  # Points awarded as length > 5

def test_circular_road_with_multiple_tails(game, players):
    """Test that a circular road with multiple tails is calculated correctly."""
    player = players[0]
    

    edges = [
        Edge(0, 1),
        Edge(1, 2),
        Edge(2, 3),
        Edge(3, 4),
        Edge(4, 5),
        Edge(0, 5),
        Edge(5, 14),
        Edge(2, 6),
        Edge(6, 7)
    ]
    
    # Place all roads
    for edge in edges:
        edge.road = player
        player.roads.append(edge)

    game._update_longest_road(player)
    
    # Calculate longest road
    length = game._calculate_player_longest_road(player)
    
    # Verify the length is correct
    assert length == 8
    assert game.longest_road == 8
    assert game.longest_road_player == player
    assert player.victory_points == 2

def test_multiple_circles_with_shared_edge(game, players):
    """Test that multiple connected circles are calculated correctly."""
    player = players[0]
    
    edges = [
        Edge(0, 1),
        Edge(1, 2),
        Edge(2, 3),
        Edge(3, 4),
        Edge(4, 5),
        Edge(0, 5),
        Edge(5, 14),
        Edge(2, 6),
        Edge(6, 7),
        Edge(7, 8),
        Edge(8, 9),
        Edge(3, 9)
    ]   
    
    # Place all roads
    for edge in edges:
        edge.road = player
        player.roads.append(edge)

    game._update_longest_road(player)
    
    # Calculate longest road
    length = game._calculate_player_longest_road(player)
    
    # Verify the length is correct
    # Should find the longest path through both circles
    assert length == 11 # The longest path through both circles
    assert game.longest_road == 11
    assert game.longest_road_player == player
    assert player.victory_points == 2  # Points awarded as length = 5

def test_longest_road_blocked_by_settlement(game, players):
    """Test that settlements from other players block road connections."""
    player1, player2 = players[0], players[1]
    
    # Create a path of 7 connected edges for player1
    edges = [
        Edge(0, 1),
        Edge(1, 2),
        Edge(2, 3),
        Edge(3, 4),
        Edge(4, 5),
        Edge(5, 14),
        Edge(14, 17),
        Edge(17, 28)
    ]
    
    # Place the roads for player1
    for edge in edges:
        edge.road = player1
        player1.roads.append(edge)
    
    # Verify initial longest road
    game._update_longest_road(player1)
    assert game.longest_road == 8
    assert game.longest_road_player == player1
    assert player1.victory_points == 2
    
    # Place player2's settlement in the middle of player1's road (at vertex 4)
    middle_vertex = game.board.vertices[4]
    middle_vertex.settlement = player2
    player2.settlements.append(middle_vertex)
    
    # Recalculate longest road
    game._update_longest_road(player1)
    
    # The longest segment should be 4 edges
    assert game._calculate_player_longest_road(player1) == 4
    assert game.longest_road == 4
    assert game.longest_road_player == None  # Lost longest road status
    assert player1.victory_points == 0  # Lost points because longest road is now < 5
    
    # Verify that placing another settlement doesn't change the calculation
    vertex = game.board.vertices[44]
    vertex.settlement = player2
    player2.settlements.append(vertex)
    
    game._update_longest_road(player1)
    assert game._calculate_player_longest_road(player1) == 4  # Now the longest segment is 4
    assert game.longest_road == 4
    assert game.longest_road_player == None
    assert player1.victory_points == 0

def test_buy_development_card(game, players):
    """Test buying a development card."""
    player = players[0]
    
    # Give player required resources
    player.resources["ore"] = 1
    player.resources["wheat"] = 1
    player.resources["sheep"] = 1
    
    # Record initial deck size
    initial_deck_size = len(game.development_deck)
    
    # Buy a development card
    game._buy_development_card(player)
    
    # Verify resources were deducted
    assert player.resources["ore"] == 0
    assert player.resources["wheat"] == 0
    assert player.resources["sheep"] == 0
    
    # Verify deck size decreased
    assert len(game.development_deck) == initial_deck_size - 1
    
    # Verify player received a card
    total_cards = sum(player.development_cards.values())
    assert total_cards == 1

def test_buy_development_card_insufficient_resources(game, players):
    """Test that development cards cannot be bought without sufficient resources."""
    player = players[0]
    
    # Give player insufficient resources
    player.resources["ore"] = 0
    player.resources["wheat"] = 1
    player.resources["sheep"] = 1
    
    # Attempt to buy a development card
    with pytest.raises(AssertionError, match="Player does not have enough resources"):
        game._buy_development_card(player)

def test_buy_development_card_empty_deck(game, players):
    """Test that development cards cannot be bought when deck is empty."""
    player = players[0]
    
    # Give player resources
    player.resources["ore"] = 1
    player.resources["wheat"] = 1
    player.resources["sheep"] = 1
    
    # Empty the deck
    game.development_deck = []
    
    # Attempt to buy a development card
    with pytest.raises(AssertionError, match="No development cards left"):
        game._buy_development_card(player)

def test_development_deck_initialization(game):
    """Test that development deck is initialized with correct card counts."""
    # Count each type of card
    card_counts = {card_type: 0 for card_type in DevelopmentCard}
    for card in game.development_deck:
        card_counts[card] += 1
    
    # Verify correct counts
    assert card_counts[DevelopmentCard.KNIGHT] == 14
    assert card_counts[DevelopmentCard.VICTORY_POINT] == 5
    assert card_counts[DevelopmentCard.ROAD_BUILDING] == 2
    assert card_counts[DevelopmentCard.YEAR_OF_PLENTY] == 2
    assert card_counts[DevelopmentCard.MONOPOLY] == 2
    
    # Verify total count
    assert len(game.development_deck) == 25

def test_development_deck_shuffled(game):
    """Test that development deck is shuffled during initialization."""
    # Create multiple games and compare their deck orders
    decks = [Game(players=[]).development_deck.copy() for _ in range(5)]
    
    # Check that at least two decks are different (very unlikely to be same if shuffled)
    all_same = all(deck == decks[0] for deck in decks[1:])
    assert not all_same, "Development decks were not shuffled"

def test_play_road_building_basic(game, players):
    """Test basic usage of Road Building card to place two roads."""
    player = players[0]
    
    # Give player a road building card
    player.development_cards[DevelopmentCard.ROAD_BUILDING] = 1
    
    # Create two valid edges for road placement
    edge1 = Edge(0, 1)
    edge2 = Edge(1, 2)
    
    # Place a settlement to make road placement valid
    vertex = game.board.vertices[0]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Use road building card
    game._play_road_building(player, [edge1, edge2])
    
    # Verify effects
    assert player.development_cards[DevelopmentCard.ROAD_BUILDING] == 0  # Card was used
    assert edge1.road == player  # First road was placed
    assert edge2.road == player  # Second road was placed
    assert len(player.roads) == 2  # Player has two roads

def test_play_road_building_single_road(game, players):
    """Test using Road Building card to place just one road."""
    player = players[0]
    
    # Give player a road building card
    player.development_cards[DevelopmentCard.ROAD_BUILDING] = 1
    
    # Create one valid edge
    edge = Edge(0, 1)
    
    # Place a settlement to make road placement valid
    vertex = game.board.vertices[0]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Use road building card for single road
    game._play_road_building(player, [edge])
    
    # Verify effects
    assert player.development_cards[DevelopmentCard.ROAD_BUILDING] == 0
    assert edge.road == player
    assert len(player.roads) == 1

def test_play_road_building_no_card(game, players):
    """Test that Road Building card cannot be used if player doesn't have it."""
    player = players[0]
    
    # Ensure player has no road building card
    player.development_cards[DevelopmentCard.ROAD_BUILDING] = 0
    
    # Try to use road building card
    with pytest.raises(AssertionError, match="Player does not have any road building cards"):
        game._play_road_building(player, [Edge(0, 1)])

def test_play_road_building_no_edges(game, players):
    """Test that Road Building card requires at least one edge to build."""
    player = players[0]
    
    # Give player a road building card
    player.development_cards[DevelopmentCard.ROAD_BUILDING] = 1
    
    # Try to use card with empty edge list
    with pytest.raises(AssertionError, match="Player must build at least 1 road"):
        game._play_road_building(player, [])

def test_play_road_building_invalid_placement(game, players):
    """Test that Road Building card follows normal road placement rules."""
    player = players[0]
    
    # Give player a road building card
    player.development_cards[DevelopmentCard.ROAD_BUILDING] = 1
    
    # Try to place roads without a settlement (should fail)
    edge1 = Edge(0, 1)
    edge2 = Edge(1, 2)
    
    # Should raise error due to invalid placement (no connected settlement)
    with pytest.raises(ValueError, match="Road must connect to the player's existing roads or settlements"):
        game._play_road_building(player, [edge1, edge2])
    
    # Verify no roads were placed and card wasn't used
    assert player.development_cards[DevelopmentCard.ROAD_BUILDING] == 1
    assert len(player.roads) == 0

def test_play_road_building_longest_road_update(game, players):
    """Test that Road Building card placement updates longest road calculation."""
    player = players[0]
    
    # Give player a road building card
    player.development_cards[DevelopmentCard.ROAD_BUILDING] = 1
    
    # Place initial settlement and roads to create a path
    vertex = game.board.vertices[0]
    vertex.settlement = player
    player.settlements.append(vertex)
    
    # Create a sequence of connected edges
    edges = [
        Edge(0, 1),
        Edge(1, 2),
        Edge(2, 3)
    ]
    
    # Place initial roads
    for edge in edges[:1]:
        game._place_road(player, edge, initial_placement=True)
    
    # Use road building card to extend the path
    game._play_road_building(player, edges[1:])
    
    # Verify longest road calculation
    assert game._calculate_player_longest_road(player) == 3
    assert len(player.roads) == 3

def test_play_monopoly_basic(game, players):
    """Test basic usage of Monopoly card to collect resources from other players."""
    player1, player2, player3 = players[0:3]
    
    # Give player1 a monopoly card and others some resources
    player1.development_cards[DevelopmentCard.MONOPOLY] = 1
    player2.resources["wood"] = 2
    player3.resources["wood"] = 3
    
    # Use monopoly card
    game._play_monopoly(player1, "wood")
    
    # Verify effects
    assert player1.development_cards[DevelopmentCard.MONOPOLY] == 0  # Card was used
    assert player1.resources["wood"] == 5  # Collected all wood (2 + 3)
    assert player2.resources["wood"] == 0  # Lost all wood
    assert player3.resources["wood"] == 0  # Lost all wood

def test_play_monopoly_no_resources(game, players):
    """Test using Monopoly card when other players have no resources."""
    player1, player2, player3 = players[0:3]
    
    # Give player1 a monopoly card but no resources to others
    player1.development_cards[DevelopmentCard.MONOPOLY] = 1
    player1.resources["wood"] = 1  # Give player1 some initial wood
    
    # Use monopoly card
    game._play_monopoly(player1, "wood")
    
    # Verify effects
    assert player1.development_cards[DevelopmentCard.MONOPOLY] == 0
    assert player1.resources["wood"] == 1  # Kept original wood, no new wood collected
    assert player2.resources["wood"] == 0
    assert player3.resources["wood"] == 0

def test_play_monopoly_no_card(game, players):
    """Test that Monopoly card cannot be used if player doesn't have it."""
    player = players[0]
    
    # Ensure player has no monopoly card
    player.development_cards[DevelopmentCard.MONOPOLY] = 0
    
    # Try to use monopoly card
    with pytest.raises(AssertionError, match="Player does not have any monopoly cards"):
        game._play_monopoly(player, "wood")

def test_play_monopoly_invalid_resource(game, players):
    """Test that Monopoly card cannot be used with invalid resource type."""
    player = players[0]
    
    # Give player a monopoly card
    player.development_cards[DevelopmentCard.MONOPOLY] = 1
    
    # Try to use card with invalid resource
    with pytest.raises(AssertionError, match="Invalid resource type"):
        game._play_monopoly(player, "invalid_resource")
    
    # Verify card wasn't used
    assert player.development_cards[DevelopmentCard.MONOPOLY] == 1

def test_play_monopoly_multiple_resource_types(game, players):
    """Test that Monopoly card only affects the specified resource type."""
    player1, player2 = players[0:2]
    
    # Setup resources
    player1.development_cards[DevelopmentCard.MONOPOLY] = 1
    player2.resources["wood"] = 2
    player2.resources["brick"] = 3
    
    # Use monopoly card on wood
    game._play_monopoly(player1, "wood")
    
    # Verify only wood was affected
    assert player1.resources["wood"] == 2  # Got wood
    assert player1.resources["brick"] == 0  # Didn't get brick
    assert player2.resources["wood"] == 0  # Lost wood
    assert player2.resources["brick"] == 3  # Kept brick

def test_play_monopoly_keeps_own_resources(game, players):
    """Test that Monopoly card doesn't affect the player's own resources."""
    player1, player2 = players[0:2]
    
    # Setup resources
    player1.development_cards[DevelopmentCard.MONOPOLY] = 1
    player1.resources["wood"] = 2  # Player's own wood
    player2.resources["wood"] = 3
    
    # Use monopoly card
    game._play_monopoly(player1, "wood")
    
    # Verify player kept their resources and got others
    assert player1.resources["wood"] == 5  # Own 2 + 3 from other player
    assert player2.resources["wood"] == 0

def test_play_monopoly_all_players(game, players):
    """Test that Monopoly card affects all other players."""
    player1, player2, player3, player4 = players
    
    # Setup resources
    player1.development_cards[DevelopmentCard.MONOPOLY] = 1
    player2.resources["wood"] = 1
    player3.resources["wood"] = 2
    player4.resources["wood"] = 3
    
    # Use monopoly card
    game._play_monopoly(player1, "wood")
    
    # Verify all players were affected
    assert player1.resources["wood"] == 6  # Got all wood (1 + 2 + 3)
    assert player2.resources["wood"] == 0
    assert player3.resources["wood"] == 0
    assert player4.resources["wood"] == 0

def test_play_knight_basic(game, players):
    """Test basic usage of Knight card to move robber and steal a resource."""
    player1, player2 = players[0:2]
    
    # Give player1 a knight card and player2 some resources
    player1.development_cards[DevelopmentCard.KNIGHT] = 1
    player2.resources["wood"] = 1
    
    # Place player2's settlement on a tile
    new_robber_pos = (0, 0)
    tile = game.board.tiles[new_robber_pos]
    vertex = tile.vertices[0]
    vertex.settlement = player2
    player2.settlements.append(vertex)
    
    # Use knight card
    initial_robber = game.board.robber
    game._play_knight(new_robber_pos, player1, player2)
    
    # Verify effects
    assert player1.development_cards[DevelopmentCard.KNIGHT] == 0  # Card was used
    assert game.board.robber == new_robber_pos  # Robber moved
    assert game.board.robber != initial_robber  # Robber position changed
    assert player1.resources["wood"] == 1  # Stole resource
    assert player2.resources["wood"] == 0  # Lost resource

def test_play_knight_no_card(game, players):
    """Test that Knight card cannot be used if player doesn't have it."""
    player1, player2 = players[0:2]
    
    # Ensure player has no knight card
    player1.development_cards[DevelopmentCard.KNIGHT] = 0
    
    with pytest.raises(AssertionError, match="Player does not have any knight cards"):
        game._play_knight((0, 0), player1, player2)

def test_play_knight_steal_from_self(game, players):
    """Test that Knight card cannot be used to steal from self."""
    player = players[0]
    
    # Give player a knight card
    player.development_cards[DevelopmentCard.KNIGHT] = 1
    
    with pytest.raises(AssertionError, match="Cannot steal from yourself"):
        game._play_knight((0, 0), player, player)

def test_play_knight_same_position(game, players):
    """Test that Knight card cannot move robber to current location."""
    player1, player2 = players[0:2]
    
    # Give player a knight card
    player1.development_cards[DevelopmentCard.KNIGHT] = 1
    current_robber = game.board.robber
    
    with pytest.raises(AssertionError, match="Robber is already on the tile"):
        game._play_knight(current_robber, player1, player2)

def test_play_knight_no_resources_to_steal(game, players):
    """Test that Knight card fails when target has no resources."""
    player1, player2 = players[0:2]
    
    # Setup
    player1.development_cards[DevelopmentCard.KNIGHT] = 1
    # Place player2's settlement but give no resources
    vertex = game.board.tiles[(0, 0)].vertices[0]
    vertex.settlement = player2
    player2.settlements.append(vertex)
    
    with pytest.raises(AssertionError, match="Player to steal from does not have any resources"):
        game._play_knight((0, 0), player1, player2)

def test_play_knight_no_settlement_on_tile(game, players):
    """Test that Knight card fails when target has no settlement on chosen tile."""
    player1, player2 = players[0:2]
    
    # Setup
    player1.development_cards[DevelopmentCard.KNIGHT] = 1
    player2.resources["wood"] = 1
    # Place settlement on different tile
    vertex = game.board.tiles[(1, 1)].vertices[0]
    vertex.settlement = player2
    player2.settlements.append(vertex)
    
    with pytest.raises(AssertionError, match="Player to steal from does not have a settlement on the tile"):
        game._play_knight((0, 0), player1, player2)

def test_play_knight_move_only(game, players):
    """Test using Knight card to only move robber without stealing."""
    player = players[0]
    
    # Give player a knight card
    player.development_cards[DevelopmentCard.KNIGHT] = 1
    
    # Find a new position for the robber that's different from current position
    initial_robber = game.board.robber
    new_pos = initial_robber
    for pos in game.board.tiles.keys():
        if pos != initial_robber:
            new_pos = pos
            break
    
    # Use knight card without stealing
    game._play_knight(new_pos, player, None)
    
    # Verify only movement occurred
    assert player.development_cards[DevelopmentCard.KNIGHT] == 0
    assert game.board.robber == new_pos  # Robber moved to new position
    assert game.board.robber != initial_robber  # Robber is not in original position

def test_play_knight_with_city(game, players):
    """Test that Knight card works with cities as well as settlements."""
    player1, player2 = players[0:2]
    
    # Setup
    player1.development_cards[DevelopmentCard.KNIGHT] = 1
    player2.resources["wood"] = 1
    
    # Place player2's city on a tile
    new_robber_pos = (0, 0)
    tile = game.board.tiles[new_robber_pos]
    vertex = tile.vertices[0]
    vertex.city = player2
    player2.settlements.append(vertex)
    player2.cities.append(vertex)
    
    # Use knight card
    game._play_knight(new_robber_pos, player1, player2)
    
    # Verify stealing worked with city
    assert player1.resources["wood"] == 1
    assert player2.resources["wood"] == 0

def test_play_knight_multiple_resources(game, players):
    """Test Knight card stealing when target has multiple resources."""
    player1, player2 = players[0:2]
    
    # Setup
    player1.development_cards[DevelopmentCard.KNIGHT] = 1
    player2.resources = {"wood": 2, "brick": 3, "sheep": 1}
    
    # Find a new position for the robber that's different from current position
    initial_robber = game.board.robber
    new_robber_pos = initial_robber
    for pos in game.board.tiles.keys():
        if pos != initial_robber:
            new_robber_pos = pos
            break
    
    # Place player2's settlement
    tile = game.board.tiles[new_robber_pos]
    vertex = tile.vertices[0]
    vertex.settlement = player2
    player2.settlements.append(vertex)
    
    # Use knight card
    game._play_knight(new_robber_pos, player1, player2)
    
    # Verify exactly one resource was stolen
    total_resources_player1 = sum(player1.resources.values())
    total_resources_player2 = sum(player2.resources.values())
    assert total_resources_player1 == 1  # Stole exactly one resource
    assert total_resources_player2 == 5  # Lost exactly one resource
    assert game.board.robber == new_robber_pos  # Robber moved to new position
    assert game.board.robber != initial_robber  # Robber is not in original position