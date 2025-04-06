import pytest
from game.game import Game
from game.player import Player
from game.board import Board, Vertex, Edge
from agent.simple_builder_agent.simple_builder_agent import SimpleAgent
from game.constants import VERTEX_PROBABILITY_SCORE, MAX_SETTLEMENTS, MAX_ROADS

@pytest.fixture
def game():
    """Create a game instance with two players for testing."""
    board = Board()
    players = [
        Player("Player 1", "red"),
        Player("Player 2", "blue")
    ]
    return Game(players)

@pytest.fixture
def agent(game):
    """Create a SimpleAgent instance for testing."""
    return SimpleAgent(game.players[0])

class TestSimpleAgentInitialization:
    """Test SimpleAgent initialization and basic attributes."""
    
    def test_agent_creation(self, agent):
        """Test that agent is created with correct player."""
        assert agent.player.name == "Player 1"
        assert agent.player.color == "red"

class TestInitialPlacement:
    """Test initial placement logic."""
    
    def test_first_turn_placement_returns_valid_actions(self, agent, game):
        """Test that first turn placement returns valid action format."""
        actions = agent.handle_initial_placement_first_turn(game)
        
        # Should return exactly two actions (settlement and road)
        assert len(actions) == 2
        
        # First action should be settlement placement
        settlement_action = actions[0]
        assert settlement_action[0] == "place_settlement"
        assert isinstance(settlement_action[1], int)  # vertex_id should be int
        
        # Second action should be road placement
        road_action = actions[1]
        assert road_action[0] == "place_road"
        assert isinstance(road_action[1], tuple)  # edge should be tuple of vertex IDs
        assert len(road_action[1]) == 2

    def test_first_turn_placement_chooses_highest_probability(self, agent, game):
        """Test that first settlement is placed on highest probability available vertex."""
        actions = agent.handle_initial_placement_first_turn(game)
        vertex_id = actions[0][1]  # Get selected vertex ID
        
        # Get the probability score of selected vertex
        selected_score = VERTEX_PROBABILITY_SCORE[vertex_id]
        
        # Check that no available vertex has a higher probability score
        for v_id, vertex in game.board.vertices.items():
            if vertex.settlement is None:  # if vertex is available
                assert VERTEX_PROBABILITY_SCORE[v_id] <= selected_score

    def test_first_turn_placement_respects_adjacency(self, agent, game):
        """Test that selected settlement location respects adjacency rules."""
        actions = agent.handle_initial_placement_first_turn(game)
        vertex_id = actions[0][1]
        vertex = game.board.vertices[vertex_id]
        
        # Check that no adjacent vertices have settlements
        for adj_vertex in vertex.adjacent_vertices:
            assert adj_vertex.settlement is None
            assert adj_vertex.city is None

    def test_first_turn_road_connects_to_settlement(self, agent, game):
        """Test that placed road connects to the placed settlement."""
        actions = agent.handle_initial_placement_first_turn(game)
        settlement_id = actions[0][1]
        road_vertices = actions[1][1]  # tuple of vertex IDs
        
        # Road should connect to settlement
        assert settlement_id in road_vertices

    def test_first_turn_placement_with_occupied_vertices(self, agent, game):
        """Test placement when some vertices are already occupied."""
        # Occupy the highest probability vertex
        highest_prob_vertex_id = max(VERTEX_PROBABILITY_SCORE.items(), key=lambda x: x[1])[0]
        game.board.vertices[highest_prob_vertex_id].settlement = game.players[1]  # other player
        
        actions = agent.handle_initial_placement_first_turn(game)
        selected_vertex_id = actions[0][1]
        
        # Should not choose occupied vertex
        assert selected_vertex_id != highest_prob_vertex_id
        # Selected vertex should be free
        assert game.board.vertices[selected_vertex_id].settlement is None

    def test_first_turn_placement_valid_road_placement(self, agent, game):
        """Test that road placement is valid."""
        actions = agent.handle_initial_placement_first_turn(game)
        road_vertices = actions[1][1]
        
        # Verify road endpoints exist
        assert road_vertices[0] in game.board.vertices
        assert road_vertices[1] in game.board.vertices
        
        # Verify vertices are adjacent
        vertex1 = game.board.vertices[road_vertices[0]]
        vertex2 = game.board.vertices[road_vertices[1]]
        assert vertex2 in vertex1.adjacent_vertices

    def test_first_turn_placement_with_all_vertices_occupied(self, agent, game):
        """Test handling when all vertices are occupied."""
        # Occupy all vertices
        for vertex in game.board.vertices.values():
            vertex.settlement = game.players[1]
            
        actions = agent.handle_initial_placement_first_turn(game)
        assert len(actions) == 0  # Should return empty list when no valid placement exists

    def test_first_turn_placement_probability_order(self, agent, game):
        """Test that vertices are considered in descending probability order."""
        actions = agent.handle_initial_placement_first_turn(game)
        selected_vertex_id = actions[0][1]
        selected_score = VERTEX_PROBABILITY_SCORE[selected_vertex_id]
        
        # Get all free vertices with higher probability scores
        higher_prob_vertices = [
            v_id for v_id, vertex in game.board.vertices.items()
            if vertex.settlement is None and VERTEX_PROBABILITY_SCORE[v_id] > selected_score
        ]
        
        # If there are any free vertices with higher probability,
        # they must be invalid due to adjacency rules
        for v_id in higher_prob_vertices:
            vertex = game.board.vertices[v_id]
            assert any(adj.settlement is not None for adj in vertex.adjacent_vertices)

    def test_second_turn_placement(self, agent, game):
        """Test second settlement and road placement."""
        actions = agent.handle_initial_placement_second_turn(game)
        
        assert len(actions) == 2
        assert actions[0][0] == "place_settlement"
        assert actions[1][0] == "place_road"

    def test_second_turn_returns_valid_actions(self, agent, game):
        """Test that second turn placement returns valid action format."""
        # First place initial settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        actions = agent.handle_initial_placement_second_turn(game)
        
        # Should return exactly two actions
        assert len(actions) == 2
        assert actions[0][0] == "place_settlement"
        assert actions[1][0] == "place_road"
        assert isinstance(actions[0][1], int)  # vertex_id
        assert isinstance(actions[1][1], tuple)  # edge vertices

    def test_second_turn_different_from_first(self, agent, game):
        """Test that second settlement is placed away from first settlement."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        # Place second settlement
        second_actions = agent.handle_initial_placement_second_turn(game)
        second_settlement_id = second_actions[0][1]
        
        # Verify settlements are different
        assert first_settlement_id != second_settlement_id
        
        # Verify not adjacent
        first_vertex = game.board.vertices[first_settlement_id]
        second_vertex = game.board.vertices[second_settlement_id]
        assert second_vertex not in first_vertex.adjacent_vertices

    def test_second_turn_resource_diversity(self, agent, game):
        """Test that second settlement considers resource diversity."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        first_vertex = game.board.vertices[first_settlement_id]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        # Get first settlement's resources
        first_resources = set()
        for tile in first_vertex.adjacent_tiles:
            first_resources.add(tile.resource_type)
        
        # Place second settlement
        second_actions = agent.handle_initial_placement_second_turn(game)
        second_settlement_id = second_actions[0][1]
        second_vertex = game.board.vertices[second_settlement_id]
        
        # Get second settlement's resources
        second_resources = set()
        for tile in second_vertex.adjacent_tiles:
            second_resources.add(tile.resource_type)
        
        # Should have some different resources
        assert second_resources - first_resources, "Second settlement should access different resources"

    def test_second_turn_placement_with_occupied_vertices(self, agent, game):
        """Test second placement when some vertices are occupied."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        # Occupy some high probability vertices
        highest_prob_vertex_id = max(VERTEX_PROBABILITY_SCORE.items(), key=lambda x: x[1])[0]
        if highest_prob_vertex_id != first_settlement_id:
            game.board.vertices[highest_prob_vertex_id].settlement = game.players[1]
        
        actions = agent.handle_initial_placement_second_turn(game)
        selected_vertex_id = actions[0][1]
        
        # Should not choose occupied vertices
        assert selected_vertex_id != highest_prob_vertex_id
        assert selected_vertex_id != first_settlement_id
        assert game.board.vertices[selected_vertex_id].settlement is None

    def test_second_turn_road_connects_to_settlement(self, agent, game):
        """Test that second road connects to second settlement."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        # Place second settlement and road
        actions = agent.handle_initial_placement_second_turn(game)
        settlement_id = actions[0][1]
        road_vertices = actions[1][1]
        
        # Road should connect to settlement
        assert settlement_id in road_vertices

    def test_second_turn_respects_adjacency_rules(self, agent, game):
        """Test that second settlement respects adjacency rules."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        # Place second settlement
        actions = agent.handle_initial_placement_second_turn(game)
        vertex_id = actions[0][1]
        vertex = game.board.vertices[vertex_id]
        
        # Check no adjacent settlements
        for adj_vertex in vertex.adjacent_vertices:
            assert adj_vertex.settlement is None
            assert adj_vertex.city is None

    def test_second_turn_with_limited_options(self, agent, game):
        """Test second placement when few vertices are available."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        # Occupy most vertices except one valid spot
        target_vertex_id = None
        for vertex_id, vertex in game.board.vertices.items():
            if vertex_id != first_settlement_id:
                # Find one valid vertex to leave open
                if target_vertex_id is None and not any(
                    adj.settlement is not None for adj in vertex.adjacent_vertices
                ):
                    target_vertex_id = vertex_id
                    continue
                vertex.settlement = game.players[1]
        
        actions = agent.handle_initial_placement_second_turn(game)
        assert actions[0][1] == target_vertex_id

    def test_second_turn_probability_consideration(self, agent, game):
        """Test that second placement still considers probability scores."""
        # Place first settlement
        first_actions = agent.handle_initial_placement_first_turn(game)
        first_settlement_id = first_actions[0][1]
        game.board.vertices[first_settlement_id].settlement = agent.player
        
        actions = agent.handle_initial_placement_second_turn(game)
        selected_vertex_id = actions[0][1]
        selected_score = VERTEX_PROBABILITY_SCORE[selected_vertex_id]
        
        # Check that any available vertex with higher probability would violate adjacency rules
        for v_id, score in VERTEX_PROBABILITY_SCORE.items():
            if score > selected_score and game.board.vertices[v_id].settlement is None:
                vertex = game.board.vertices[v_id]
                # Must either be adjacent to first settlement or have adjacent settlement
                assert (
                    vertex in game.board.vertices[first_settlement_id].adjacent_vertices or
                    any(adj.settlement is not None for adj in vertex.adjacent_vertices)
                )

class TestBuildingLogic:
    """Test building decision logic."""
    
    def test_can_build_settlement(self, agent):
        """Test settlement building requirements."""
        # Initially shouldn't have resources
        assert not agent._can_build_settlement()
        
        # Add required resources
        agent.player.resources.update({
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1
        })
        assert agent._can_build_settlement()
        
        # Test settlement limit
        for _ in range(5):  # MAX_SETTLEMENTS
            agent.player.settlements.append(Vertex(0))
        assert not agent._can_build_settlement()

    def test_can_build_road(self, agent):
        """Test road building requirements."""
        assert not agent._can_build_road()
        
        agent.player.resources.update({
            "wood": 1,
            "brick": 1
        })
        assert agent._can_build_road()

    def test_can_build_city(self, agent):
        """Test city building requirements."""
        assert not agent._can_build_city()
        
        agent.player.resources.update({
            "wheat": 2,
            "ore": 3
        })
        assert agent._can_build_city()

class TestRobberLogic:
    """Test robber movement logic."""
    
    def test_robber_targeting(self, agent, game):
        """Test robber movement and player targeting."""
        # Give second player more points
        game.players[1].victory_points = 5
        
        result = agent.handle_robber_move(game)
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        coords, target_player = result
        assert isinstance(coords, tuple)
        assert len(coords) == 2
        assert target_player == game.players[1]

    def test_robber_avoids_own_settlements(self, agent, game):
        """Test that robber avoids tiles with agent's settlements."""
        # Place agent's settlement
        vertex = list(game.board.vertices.values())[0]
        vertex.settlement = agent.player
        tile = vertex.adjacent_tiles[0]
        
        result = agent.handle_robber_move(game)
        coords, _ = result
        assert coords != tile.cord

class TestVertexSelection:
    """Test vertex selection logic."""
    
    def test_vertex_is_free(self, agent, game):
        """Test vertex availability checking."""
        vertex = list(game.board.vertices.values())[0]
        assert agent._vertex_is_free(vertex)
        
        vertex.settlement = agent.player
        assert not agent._vertex_is_free(vertex)
        
        vertex.settlement = None
        vertex.city = agent.player
        assert not agent._vertex_is_free(vertex)

    def test_find_valid_settlement_spot(self, agent, game):
        """Test finding valid settlement location."""
        # Add a road to the agent
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        spot = agent._find_valid_settlement_spot(game)
        assert spot is not None
        assert isinstance(spot, int)
        assert spot in game.board.vertices

class TestTurnActions:
    """Test turn action decision making."""
    
    def test_no_actions_without_resources(self, agent, game):
        """Test that no actions are returned without resources."""
        actions = agent.decide_turn_actions(game)
        assert len(actions) == 0

    def test_settlement_priority(self, agent, game):
        """Test that settlement building is prioritized."""
        # Give resources for all building types
        agent.player.resources.update({
            "wood": 2,
            "brick": 2,
            "sheep": 1,
            "wheat": 3,
            "ore": 3
        })
        
        # Add a road to enable settlement building
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        actions = agent.decide_turn_actions(game)
        assert len(actions) > 0
        assert actions[0][0] == "place_settlement"

class TestSettlementBuilding:
    """Test settlement building validation logic."""

    def test_can_build_settlement_no_resources(self, agent):
        """Test settlement building with no resources."""
        # Initial state should have no resources
        agent.player.resources = {
            "wood": 0,
            "brick": 0,
            "sheep": 0,
            "wheat": 0,
            "ore": 0
        }
        assert not agent._can_build_settlement()

    def test_can_build_settlement_partial_resources(self, agent):
        """Test settlement building with incomplete resources."""
        # Test various partial resource combinations
        resource_combinations = [
            {"wood": 1, "brick": 1, "sheep": 1, "wheat": 0},  # Missing wheat
            {"wood": 1, "brick": 1, "sheep": 0, "wheat": 1},  # Missing sheep
            {"wood": 1, "brick": 0, "sheep": 1, "wheat": 1},  # Missing brick
            {"wood": 0, "brick": 1, "sheep": 1, "wheat": 1},  # Missing wood
        ]
        
        for resources in resource_combinations:
            agent.player.resources = {**{"ore": 0}, **resources}
            assert not agent._can_build_settlement(), f"Should not build with resources: {resources}"

    def test_can_build_settlement_exact_resources(self, agent):
        """Test settlement building with exact required resources."""
        agent.player.resources = {
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1,
            "ore": 0
        }
        assert agent._can_build_settlement()

    def test_can_build_settlement_excess_resources(self, agent):
        """Test settlement building with more than required resources."""
        agent.player.resources = {
            "wood": 2,
            "brick": 3,
            "sheep": 2,
            "wheat": 2,
            "ore": 1
        }
        assert agent._can_build_settlement()

    def test_can_build_settlement_at_limit(self, agent):
        """Test settlement building when at settlement limit."""
        # Add required resources
        agent.player.resources = {
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1,
            "ore": 0
        }
        
        # Add settlements up to limit
        for i in range(MAX_SETTLEMENTS):
            agent.player.settlements.append(Vertex(i))
            
        assert not agent._can_build_settlement()

    def test_can_build_settlement_approaching_limit(self, agent):
        """Test settlement building when approaching settlement limit."""
        # Add required resources
        agent.player.resources = {
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1,
            "ore": 0
        }
        
        # Add settlements up to one less than limit
        for i in range(MAX_SETTLEMENTS - 1):
            agent.player.settlements.append(Vertex(i))
            
        assert agent._can_build_settlement()

    def test_can_build_settlement_resource_edge_cases(self, agent):
        """Test settlement building with edge case resource amounts."""
        edge_cases = [
            # Negative resources (invalid game state, but should handle gracefully)
            {
                "wood": -1,
                "brick": 1,
                "sheep": 1,
                "wheat": 1
            },
            # Very large numbers
            {
                "wood": 1000,
                "brick": 1000,
                "sheep": 1000,
                "wheat": 1000
            },
            # Zero of unused resource
            {
                "wood": 1,
                "brick": 1,
                "sheep": 1,
                "wheat": 1,
                "ore": 0
            }
        ]
        
        for resources in edge_cases:
            agent.player.resources = resources
            expected = all(resources.get(r, 0) >= 1 for r in ["wood", "brick", "sheep", "wheat"])
            assert agent._can_build_settlement() == expected

    def test_can_build_settlement_missing_resource_keys(self, agent):
        """Test settlement building with missing resource dictionary keys."""
        # Missing some resource keys (should handle gracefully)
        agent.player.resources = {
            "wood": 1,
            "brick": 1
            # Missing sheep and wheat
        }
        assert not agent._can_build_settlement()

    def test_can_build_settlement_resource_types(self, agent):
        """Test that only correct resource types are considered."""
        # Add invalid resource type
        agent.player.resources = {
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1,
            "invalid_resource": 10  # Should be ignored
        }
        assert agent._can_build_settlement()

    def test_can_build_settlement_after_removal(self, agent):
        """Test settlement building after removing a settlement."""
        # Fill up to limit
        agent.player.resources = {
            "wood": 1,
            "brick": 1,
            "sheep": 1,
            "wheat": 1
        }
        for i in range(MAX_SETTLEMENTS):
            agent.player.settlements.append(Vertex(i))
        
        assert not agent._can_build_settlement()
        
        # Remove one settlement
        agent.player.settlements.pop()
        assert agent._can_build_settlement()

class TestValidSettlementSpot:
    """Test finding valid settlement locations."""

    def test_find_valid_settlement_spot_no_roads(self, agent, game):
        """Test finding settlement spot with no roads placed."""
        # Without any roads, should not find a valid spot
        assert agent._find_valid_settlement_spot(game) is None

    def test_find_valid_settlement_spot_with_road(self, agent, game):
        """Test finding settlement spot with a road placed."""
        # Place a road
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        # Should find one of the road endpoints
        spot = agent._find_valid_settlement_spot(game)
        assert spot is not None
        assert spot in edge.vertices

    def test_find_valid_settlement_spot_with_adjacent_settlement(self, agent, game):
        """Test that spots adjacent to settlements are invalid."""
        # Place a road
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        # Place settlement adjacent to road endpoint
        vertex = game.board.vertices[edge.vertices[0]]
        adjacent_vertex = vertex.adjacent_vertices[0]
        adjacent_vertex.settlement = game.players[1]  # Other player's settlement
        
        # If the only available spot is adjacent to a settlement, should return None
        if all(adj.settlement is not None for v in edge.vertices 
               for adj in game.board.vertices[v].adjacent_vertices):
            assert agent._find_valid_settlement_spot(game) is None
        else:
            # Should find a spot that's not adjacent to the settlement
            spot = agent._find_valid_settlement_spot(game)
            assert spot is not None
            vertex = game.board.vertices[spot]
            assert all(adj.settlement is None for adj in vertex.adjacent_vertices)

    def test_find_valid_settlement_spot_with_multiple_roads(self, agent, game):
        """Test finding settlement spot with multiple roads."""
        # Place two connected roads
        edges = list(game.board.edges.values())
        edge1 = edges[0]
        edge1.road = agent.player
        agent.player.roads.append(edge1)
        
        # Find a connected edge
        for edge in edges[1:]:
            if any(v in edge1.vertices for v in edge.vertices):
                edge2 = edge
                break
        
        edge2.road = agent.player
        agent.player.roads.append(edge2)
        
        # Should find one of the road endpoints
        spot = agent._find_valid_settlement_spot(game)
        assert spot is not None
        assert any(spot in edge.vertices for edge in [edge1, edge2])

    def test_find_valid_settlement_spot_with_existing_settlement(self, agent, game):
        """Test finding spot when player has existing settlements."""
        # Place a settlement
        vertex = list(game.board.vertices.values())[0]
        vertex.settlement = agent.player
        agent.player.settlements.append(vertex)
        
        # Place a road connected to settlement
        for edge in game.board.edges.values():
            if vertex.id in edge.vertices:
                edge.road = agent.player
                agent.player.roads.append(edge)
                break
        
        # Should find a spot that's not the existing settlement
        spot = agent._find_valid_settlement_spot(game)
        assert spot is not None
        assert spot != vertex.id
        assert not any(adj.settlement is not None 
                      for adj in game.board.vertices[spot].adjacent_vertices)

    def test_find_valid_settlement_spot_fully_occupied(self, agent, game):
        """Test when all potential spots are occupied."""
        # Place a road
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        # Occupy all vertices connected to the road
        for vertex_id in edge.vertices:
            vertex = game.board.vertices[vertex_id]
            vertex.settlement = game.players[1]
        
        assert agent._find_valid_settlement_spot(game) is None

    def test_find_valid_settlement_spot_with_cities(self, agent, game):
        """Test that cities are considered as occupied spots."""
        # Place a road
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        # Place a city at one endpoint
        vertex = game.board.vertices[edge.vertices[0]]
        vertex.city = game.players[1]
        
        # Should not select the vertex with the city
        spot = agent._find_valid_settlement_spot(game)
        if spot is not None:  # Might be None if no valid spots
            assert spot != vertex.id

    def test_find_valid_settlement_spot_connected_network(self, agent, game):
        """Test that spots must be connected to road network."""
        # Place two unconnected roads
        edges = list(game.board.edges.values())
        edge1 = edges[0]
        edge1.road = agent.player
        agent.player.roads.append(edge1)
        
        # Find an unconnected edge
        for edge in edges[1:]:
            if not any(v in edge1.vertices for v in edge.vertices):
                edge2 = edge
                break
        
        edge2.road = agent.player
        agent.player.roads.append(edge2)
        
        # The returned spot should be connected to one of our roads
        spot = agent._find_valid_settlement_spot(game)
        if spot is not None:
            assert any(v in spot for road in agent.player.roads for v in road.vertices)

    def test_find_valid_settlement_spot_prioritization(self, agent, game):
        """Test that the first valid spot is returned."""
        # Place a road
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        
        # Get the first valid spot
        first_spot = agent._find_valid_settlement_spot(game)
        
        # Running it again should return the same spot
        # (assuming deterministic iteration order)
        second_spot = agent._find_valid_settlement_spot(game)
        
        assert first_spot == second_spot

class TestVertexAvailability:
    """Test vertex availability checking."""

    def test_vertex_is_free_empty_vertex(self, agent, game):
        """Test that a completely empty vertex is considered free."""
        vertex = list(game.board.vertices.values())[0]
        vertex.settlement = None
        vertex.city = None
        
        assert agent._vertex_is_free(vertex)

    def test_vertex_is_free_with_settlement(self, agent, game):
        """Test that a vertex with a settlement is not free."""
        vertex = list(game.board.vertices.values())[0]
        
        # Test with own settlement
        vertex.settlement = agent.player
        assert not agent._vertex_is_free(vertex)
        
        # Test with other player's settlement
        vertex.settlement = game.players[1]
        assert not agent._vertex_is_free(vertex)

    def test_vertex_is_free_with_city(self, agent, game):
        """Test that a vertex with a city is not free."""
        vertex = list(game.board.vertices.values())[0]
        
        # Test with own city
        vertex.city = agent.player
        assert not agent._vertex_is_free(vertex)
        
        # Test with other player's city
        vertex.city = game.players[1]
        assert not agent._vertex_is_free(vertex)

    def test_vertex_is_free_after_removal(self, agent, game):
        """Test that a vertex becomes free after removing buildings."""
        vertex = list(game.board.vertices.values())[0]
        
        # Test settlement removal
        vertex.settlement = agent.player
        assert not agent._vertex_is_free(vertex)
        vertex.settlement = None
        assert agent._vertex_is_free(vertex)
        
        # Test city removal
        vertex.city = agent.player
        assert not agent._vertex_is_free(vertex)
        vertex.city = None
        assert agent._vertex_is_free(vertex)

    def test_vertex_is_free_invalid_state(self, agent, game):
        """Test vertex with invalid state (both settlement and city)."""
        vertex = list(game.board.vertices.values())[0]
        
        # Invalid game state: both settlement and city
        vertex.settlement = agent.player
        vertex.city = agent.player
        assert not agent._vertex_is_free(vertex)
        
        vertex.settlement = game.players[1]
        vertex.city = agent.player
        assert not agent._vertex_is_free(vertex)

    def test_vertex_is_free_multiple_checks(self, agent, game):
        """Test that multiple checks on the same vertex are consistent."""
        vertex = list(game.board.vertices.values())[0]
        
        # Multiple checks should return the same result
        assert agent._vertex_is_free(vertex) == agent._vertex_is_free(vertex)
        
        vertex.settlement = agent.player
        assert not agent._vertex_is_free(vertex)
        assert not agent._vertex_is_free(vertex)

    def test_vertex_is_free_different_vertices(self, agent, game):
        """Test that different vertices are evaluated independently."""
        vertex1 = list(game.board.vertices.values())[0]
        vertex2 = list(game.board.vertices.values())[1]
        
        # Both should start free
        assert agent._vertex_is_free(vertex1)
        assert agent._vertex_is_free(vertex2)
        
        # Occupying one shouldn't affect the other
        vertex1.settlement = agent.player
        assert not agent._vertex_is_free(vertex1)
        assert agent._vertex_is_free(vertex2)

    def test_vertex_is_free_edge_cases(self, agent, game):
        """Test edge cases and unusual situations."""
        vertex = list(game.board.vertices.values())[0]
        
        # Test with None player reference
        vertex.settlement = None
        vertex.city = None
        assert agent._vertex_is_free(vertex)
        
        # Test with empty player reference
        vertex.settlement = Player("", "")
        assert not agent._vertex_is_free(vertex)
        
        # Test with deleted/invalid player reference
        vertex.settlement = "invalid_player"
        assert not agent._vertex_is_free(vertex)

    def test_vertex_is_free_type_safety(self, agent, game):
        """Test type safety of the vertex checking."""
        vertex = list(game.board.vertices.values())[0]
        
        # Test with various attribute types
        test_values = [
            0,              # int
            "",            # empty string
            "settlement",  # string
            [],           # empty list
            {},           # empty dict
            True,         # boolean
            object(),     # generic object
        ]
        
        for value in test_values:
            vertex.settlement = value
            assert not agent._vertex_is_free(vertex)
            vertex.settlement = None
            
            vertex.city = value
            assert not agent._vertex_is_free(vertex)
            vertex.city = None

    def test_vertex_is_free_attribute_access(self, agent, game):
        """Test that the method properly accesses vertex attributes."""
        vertex = list(game.board.vertices.values())[0]
        
        # Remove attributes to test attribute error handling
        if hasattr(vertex, 'settlement'):
            delattr(vertex, 'settlement')
        if hasattr(vertex, 'city'):
            delattr(vertex, 'city')
            
        # Should handle missing attributes gracefully or raise appropriate error
        with pytest.raises(AttributeError):
            agent._vertex_is_free(vertex)

class TestRoadBuilding:
    """Test road building validation and placement logic."""

    def test_can_build_road_no_resources(self, agent):
        """Test road building with no resources."""
        agent.player.resources = {
            "wood": 0,
            "brick": 0,
            "sheep": 0,
            "wheat": 0,
            "ore": 0
        }
        assert not agent._can_build_road()

    def test_can_build_road_partial_resources(self, agent):
        """Test road building with partial resources."""
        # Test having only wood
        agent.player.resources = {"wood": 1, "brick": 0}
        assert not agent._can_build_road()
        
        # Test having only brick
        agent.player.resources = {"wood": 0, "brick": 1}
        assert not agent._can_build_road()

    def test_can_build_road_exact_resources(self, agent):
        """Test road building with exact required resources."""
        agent.player.resources = {"wood": 1, "brick": 1}
        assert agent._can_build_road()

    def test_can_build_road_at_limit(self, agent):
        """Test road building when at road limit."""
        agent.player.resources = {"wood": 1, "brick": 1}
        
        # Add roads up to limit
        for _ in range(MAX_ROADS):
            agent.player.roads.append(Edge(0, 1))
            
        assert not agent._can_build_road()

    def test_can_build_road_approaching_limit(self, agent):
        """Test road building when approaching road limit."""
        agent.player.resources = {"wood": 1, "brick": 1}
        
        # Add roads up to one less than limit
        for _ in range(MAX_ROADS - 1):
            agent.player.roads.append(Edge(0, 1))
            
        assert agent._can_build_road()

class TestValidRoadSpot:
    """Test finding valid road locations."""

    @pytest.fixture
    def setup_initial_road(self, agent, game):
        """Setup fixture with initial road placement."""
        edge = list(game.board.edges.values())[0]
        edge.road = agent.player
        agent.player.roads.append(edge)
        return edge

    def test_find_valid_road_spot_no_roads_or_settlements(self, agent, game):
        """Test finding road spot with no existing roads or settlements."""
        assert agent._find_valid_road_spot(game) is None

    def test_find_valid_road_spot_with_existing_road(self, agent, game, setup_initial_road):
        """Test finding road spot connected to existing road."""
        spot = agent._find_valid_road_spot(game)
        assert spot is not None
        assert isinstance(spot, tuple)
        assert len(spot) == 2
        
        # Verify spot connects to existing road
        initial_road = setup_initial_road
        assert any(v in initial_road.vertices for v in spot)

    def test_find_valid_road_spot_with_occupied_edges(self, agent, game, setup_initial_road):
        """Test finding road spot when adjacent edges are occupied."""
        # Occupy all adjacent edges
        initial_road = setup_initial_road
        for v_id in initial_road.vertices:
            vertex = game.board.vertices[v_id]
            for adj_vertex in vertex.adjacent_vertices:
                edge_id = tuple(sorted((v_id, adj_vertex.id)))
                if edge_id in game.board.edges:
                    game.board.edges[edge_id].road = game.players[1]
        
        assert agent._find_valid_road_spot(game) is None

    def test_find_valid_road_spot_multiple_roads(self, agent, game, setup_initial_road):
        """Test finding road spot with multiple existing roads."""
        # Add second road connected to first
        initial_road = setup_initial_road
        v_id = initial_road.vertices[0]
        vertex = game.board.vertices[v_id]
        
        for adj_vertex in vertex.adjacent_vertices:
            edge_id = tuple(sorted((v_id, adj_vertex.id)))
            if edge_id in game.board.edges and game.board.edges[edge_id].road is None:
                edge = game.board.edges[edge_id]
                edge.road = agent.player
                agent.player.roads.append(edge)
                break
        
        spot = agent._find_valid_road_spot(game)
        assert spot is not None
        # Verify spot connects to road network
        assert any(v in spot for road in agent.player.roads for v in road.vertices)

    def test_find_valid_road_spot_edge_sorting(self, agent, game, setup_initial_road):
        """Test that returned edge vertices are properly sorted."""
        spot = agent._find_valid_road_spot(game)
        if spot is not None:
            assert spot[0] < spot[1], "Edge vertices should be sorted"

    def test_find_valid_road_spot_with_settlement(self, agent, game):
        """Test finding road spot connected to settlement."""
        # Place a settlement
        vertex = list(game.board.vertices.values())[0]
        vertex.settlement = agent.player
        agent.player.settlements.append(vertex)
        
        spot = agent._find_valid_road_spot(game)
        assert spot is not None
        assert vertex.id in spot

    def test_find_valid_road_spot_invalid_edges(self, agent, game, setup_initial_road):
        """Test handling of invalid edge coordinates."""
        # Add invalid edge to candidate set (implementation detail test)
        initial_road = setup_initial_road
        v_id = initial_road.vertices[0]
        invalid_edge = (v_id, 9999)  # Invalid vertex ID
        
        spot = agent._find_valid_road_spot(game)
        assert spot is not None
        assert spot != invalid_edge

    def test_find_valid_road_spot_disconnected_roads(self, agent, game):
        """Test finding road spot with disconnected road network."""
        # Place two unconnected roads
        edges = list(game.board.edges.values())
        
        # Find two unconnected edges
        edge1 = edges[0]
        edge1.road = agent.player
        agent.player.roads.append(edge1)
        
        for edge in edges[1:]:
            if not any(v in edge1.vertices for v in edge.vertices):
                edge2 = edge
                edge2.road = agent.player
                agent.player.roads.append(edge2)
                break
        
        spot = agent._find_valid_road_spot(game)
        assert spot is not None
        # Spot should connect to one of the existing roads
        assert any(v in spot for road in agent.player.roads for v in road.vertices)

    def test_find_valid_road_spot_performance(self, agent, game):
        """Test performance with large road network."""
        # Add multiple roads to create a larger network
        edges = list(game.board.edges.values())[:10]  # Limit to 10 roads for test
        for edge in edges:
            edge.road = agent.player
            agent.player.roads.append(edge)
        
        # Ensure method returns in reasonable time
        import time
        start_time = time.time()
        spot = agent._find_valid_road_spot(game)
        end_time = time.time()
        
        assert end_time - start_time < 1.0  # Should complete within 1 second
        assert spot is not None

class TestComplexRoadNetworks:
    """Test road placement with complex network configurations."""

    def create_network(self, agent, game, network_config):
        """Helper to create a specific road network configuration."""
        for v1_id, v2_id, owner in network_config:
            edge_id = tuple(sorted((v1_id, v2_id)))
            if edge_id in game.board.edges:
                edge = game.board.edges[edge_id]
                edge.road = owner
                if owner == agent.player:
                    agent.player.roads.append(edge)

    def test_branching_network(self, agent, game):
        """Test road placement in a branching network configuration.
        
        Network shape:
              B
              |
        B--A--P--A--B
              |
              B
        
        P = Player's roads
        A = Available edges
        B = Blocked edges (other players)
        """
        # Create a branching network centered at vertex 20
        network_config = [
            (20, 21, agent.player),    # Center right
            (20, 19, agent.player),    # Center left
            (20, 25, agent.player),    # Center up
            (20, 15, agent.player),    # Center down
            (21, 22, game.players[1]), # Right blocked
            (19, 18, game.players[1]), # Left blocked
            (25, 30, game.players[1]), # Up blocked
            (15, 10, game.players[1])  # Down blocked
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        assert valid_spot is not None
        # Should find one of the available spots adjacent to player's network
        assert any(v == 20 for v in valid_spot)

    def test_circular_network(self, agent, game):
        """Test road placement in a circular network configuration.
        
        Network shape:
           P--P
           |  |
           P--A
        
        P = Player's roads
        A = Available edge
        """
        network_config = [
            (20, 21, agent.player),  # Top
            (21, 26, agent.player),  # Right
            (20, 25, agent.player),  # Left
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        assert valid_spot is not None
        # Should complete the circle
        assert tuple(sorted((25, 26))) == valid_spot

    def test_interleaved_network(self, agent, game):
        """Test road placement with interleaved player roads.
        
        Network shape:
        P--B--P--B--P
        
        P = Player's roads
        B = Blocked edges (other players)
        """
        network_config = [
            (20, 21, agent.player),     # First player road
            (21, 22, game.players[1]),  # Blocked
            (22, 23, agent.player),     # Second player road
            (23, 24, game.players[1]),  # Blocked
            (24, 25, agent.player),     # Third player road
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        assert valid_spot is not None
        # Should find a spot connected to one of player's roads
        assert any(any(v in road.vertices for v in valid_spot) 
                  for road in agent.player.roads)

    def test_complex_intersection(self, agent, game):
        """Test road placement at complex intersection.
        
        Network shape:
           B  P  B
           |  |  |
        B--P--*--P--B
           |  |  |
           B  P  B
        
        * = Center intersection
        P = Player's roads
        B = Blocked edges (other players)
        """
        center = 20
        network_config = [
            # Player's cross
            (center, center+1, agent.player),  # Right
            (center, center-1, agent.player),  # Left
            (center, center+5, agent.player),  # Up
            (center, center-5, agent.player),  # Down
            # Blocking roads
            (center+1, center+2, game.players[1]),  # Far right
            (center-1, center-2, game.players[1]),  # Far left
            (center+5, center+10, game.players[1]), # Far up
            (center-5, center-10, game.players[1]), # Far down
            # Diagonal blocks
            (center+6, center+1, game.players[1]),
            (center+4, center-1, game.players[1]),
            (center-6, center+1, game.players[1]),
            (center-4, center-1, game.players[1])
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        if valid_spot is not None:
            # Should find a spot connected to player's cross
            assert any(center in edge.vertices for edge in agent.player.roads)

    def test_parallel_networks(self, agent, game):
        """Test road placement with parallel networks.
        
        Network shape:
        P--P--P
        |  |  |
        B--B--B
        |  |  |
        P--P--P
        """
        network_config = [
            # Top row
            (20, 21, agent.player),
            (21, 22, agent.player),
            # Bottom row
            (25, 26, agent.player),
            (26, 27, agent.player),
            # Middle blocking row
            (22, 23, game.players[1]),
            (23, 24, game.players[1]),
            # Vertical connections
            (20, 25, agent.player),
            (21, 26, agent.player),
            (22, 27, agent.player)
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        assert valid_spot is not None
        # Should find a spot that extends one of the parallel networks
        assert any(any(v in road.vertices for v in valid_spot) 
                  for road in agent.player.roads)

    def test_network_with_settlements(self, agent, game):
        """Test road placement with settlements in the network.
        
        Network shape:
        S--P--P--S
           |
           P--S
        
        S = Settlements
        P = Player's roads
        """
        # Place settlements
        settlements = [20, 23, 26]  # Vertex IDs
        for vertex_id in settlements:
            vertex = game.board.vertices[vertex_id]
            vertex.settlement = agent.player
            agent.player.settlements.append(vertex)
        
        # Create road network
        network_config = [
            (20, 21, agent.player),
            (21, 22, agent.player),
            (22, 23, agent.player),
            (21, 26, agent.player)
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        assert valid_spot is not None
        # Should find a spot that connects to either a road or settlement
        assert (any(any(v in road.vertices for v in valid_spot) for road in agent.player.roads) or
                any(v in settlements for v in valid_spot))

    def test_network_bottleneck(self, agent, game):
        """Test road placement through a bottleneck.
        
        Network shape:
        P--P--*--B--S
              |
              B
        
        * = Bottleneck
        P = Player's roads
        B = Blocked edges
        S = Target settlement location
        """
        # Place settlement
        target_settlement = game.board.vertices[24]
        target_settlement.settlement = agent.player
        agent.player.settlements.append(target_settlement)
        
        network_config = [
            (20, 21, agent.player),    # Player's initial roads
            (21, 22, agent.player),
            (22, 23, game.players[1]), # Blocking road
            (23, 24, game.players[1]), # Blocking road to settlement
            (22, 27, game.players[1])  # Blocking side road
        ]
        self.create_network(agent, game, network_config)
        
        valid_spot = agent._find_valid_road_spot(game)
        assert valid_spot is not None
        # Should find a path around the bottleneck
        assert any(v == 22 for v in valid_spot)

class TestComplexRobberScenarios:
    """Advanced test scenarios for robber movement and targeting."""
    
    def setup_board_state(self, game, settlements_config, cities_config=None, robber_pos=(0, 0)):
        """Helper to set up complex board states.
        settlements_config: {(x, y): [(player_idx, vertex_idx), ...]}
        cities_config: {(x, y): [(player_idx, vertex_idx), ...]}
        """
        game.board.robber = robber_pos
        for tile_coord, settlements in settlements_config.items():
            tile = game.board.tiles[tile_coord]
            for player_idx, vertex_idx in settlements:
                tile.vertices[vertex_idx].settlement = game.players[player_idx]
        
        if cities_config:
            for tile_coord, cities in cities_config.items():
                tile = game.board.tiles[tile_coord]
                for player_idx, vertex_idx in cities:
                    tile.vertices[vertex_idx].city = game.players[player_idx]
                    tile.vertices[vertex_idx].settlement = None

    def test_complex_resource_cluster(self, agent, game):
        """Test targeting a cluster of high-value resources with multiple players."""
        # Set up a resource cluster with multiple players
        settlements_config = {
            (2, 2): [(1, 0), (2, 1)],  # High-value tile with two players
            (2, 3): [(1, 0), (3, 1)],  # Adjacent tile with different players
            (3, 2): [(2, 0), (3, 1)]   # Completing the cluster
        }
        
        self.setup_board_state(game, settlements_config)
        self.setup_player_points(game, [2, 5, 4, 3])
        
        move = agent.handle_robber_move(game)
        
        # Should target the cluster tile with highest point player
        assert move[0] == (2, 2)
        assert move[1] == game.players[1]

    def test_resource_denial_strategy(self, agent, game):
        """Test denying crucial resources to leading player."""
        # Set up a board where leading player has settlements on key resources
        settlements_config = {
            (1, 1): [(1, 0)],  # Ore (crucial for cities)
            (2, 2): [(1, 0)],  # Wheat (crucial for cities/development)
            (3, 3): [(1, 0)],  # Wood (less crucial)
        }
        
        # Add cities to make the resource more valuable
        cities_config = {
            (1, 1): [(1, 1)],  # City on ore
        }
        
        self.setup_board_state(game, settlements_config, cities_config)
        self.setup_player_points(game, [2, 6, 3, 4])
        
        move = agent.handle_robber_move(game)
        
        # Should prioritize blocking ore/wheat over wood
        assert move[0] in [(1, 1), (2, 2)]
        assert move[1] == game.players[1]

    def test_mixed_settlement_city_configuration(self, agent, game):
        """Test handling mixed settlements and cities on the same tile."""
        settlements_config = {
            (2, 2): [(1, 0), (2, 1)],  # Two settlements
        }
        
        cities_config = {
            (2, 2): [(3, 2)],          # One city on same tile
            (3, 3): [(1, 0)]           # Isolated city
        }
        
        self.setup_board_state(game, settlements_config, cities_config)
        self.setup_player_points(game, [2, 5, 3, 4])
        
        move = agent.handle_robber_move(game)
        
        # Should prefer tile with most development (settlements + cities)
        assert move[0] == (2, 2)
        assert move[1] == game.players[1]

    def test_robber_movement_restrictions(self, agent, game):
        """Test robber movement with various restrictions and obstacles."""
        # Set up complex board with restricted movement options
        settlements_config = {
            (0, 0): [(0, 0)],  # Our settlement
            (1, 1): [(1, 0)],  # Target player
            (2, 2): [(0, 0), (1, 1)],  # Mixed ownership
            (3, 3): [(2, 0)]   # Other player
        }
        
        # Current robber position
        current_robber = (1, 1)
        self.setup_board_state(game, settlements_config, robber_pos=current_robber)
        self.setup_player_points(game, [2, 5, 3, 4])
        
        move = agent.handle_robber_move(game)
        
        # Should not stay in current position
        assert move[0] != current_robber
        # Should not move to tile with only our settlements
        assert move[0] != (0, 0)

    def test_city_development_blocking(self, agent, game):
        """Test blocking potential city development."""
        settlements_config = {
            (1, 1): [(1, 0)],  # Regular settlement
        }
        
        cities_config = {
            (2, 2): [(1, 0)],  # Existing city
            (3, 3): [(1, 0)]   # Another city
        }
        
        self.setup_board_state(game, settlements_config, cities_config)
        self.setup_player_points(game, [2, 7, 3, 4])
        
        # Target player has resources for another city
        game.players[1].resources = {'ore': 3, 'wheat': 2}
        
        move = agent.handle_robber_move(game)
        
        # Should target settlement that could become city
        assert move[0] == (1, 1)
        assert move[1] == game.players[1]

    def test_complex_network_blocking(self, agent, game):
        """Test blocking strategic positions in road networks."""
        # Set up a complex road network with settlements
        settlements_config = {
            (1, 1): [(1, 0)],  # Start of network
            (2, 2): [(1, 1)],  # Middle of network
            (3, 3): [(1, 2)]   # End of network
        }
        
        # Add roads connecting settlements
        for i in range(3):
            edge = game.board.edges[tuple(sorted((i, i+1)))]
            edge.road = game.players[1]
        
        self.setup_board_state(game, settlements_config)
        self.setup_player_points(game, [2, 5, 3, 4])
        
        move = agent.handle_robber_move(game)
        
        # Should target middle of network to maximize disruption
        assert move[0] == (2, 2)
        assert move[1] == game.players[1]

    def test_resource_monopoly_breaking(self, agent, game):
        """Test breaking up resource monopolies."""
        # Set up a player with monopoly on ore
        settlements_config = {
            (1, 1): [(1, 0)],  # Ore
            (1, 2): [(1, 0)],  # Ore
            (1, 3): [(1, 0)],  # Ore
            (2, 1): [(1, 0)]   # Different resource
        }
        
        cities_config = {
            (1, 1): [(1, 0)],  # City on ore
        }
        
        self.setup_board_state(game, settlements_config, cities_config)
        self.setup_player_points(game, [2, 6, 3, 4])
        
        move = agent.handle_robber_move(game)
        
        # Should target ore monopoly, preferably tile with city
        assert move[0] == (1, 1)
        assert move[1] == game.players[1]

    def test_endgame_blocking_strategy(self, agent, game):
        """Test blocking strategy when player is close to winning."""
        settlements_config = {
            (1, 1): [(1, 0)],
            (2, 2): [(1, 1)]
        }
        
        cities_config = {
            (3, 3): [(1, 0)],
            (4, 4): [(1, 1)]
        }
        
        self.setup_board_state(game, settlements_config, cities_config)
        self.setup_player_points(game, [2, 9, 3, 4])  # Target player close to winning
        
        # Give target player resources for potential victory point
        game.players[1].resources = {'ore': 3, 'wheat': 2}
        
        move = agent.handle_robber_move(game)
        
        # Should prioritize blocking crucial resources
        assert move[0] in [(1, 1), (2, 2)]  # Target resource-generating tiles
        assert move[1] == game.players[1]

    def test_desert_tile_handling(self, agent, game):
        """Test proper handling of desert tile in various scenarios."""
        settlements_config = {
            (0, 0): [(1, 0)],  # Desert tile
            (1, 1): [(1, 0)],  # Regular tile
        }
        
        # Mark (0, 0) as desert
        game.board.tiles[(0, 0)].resource = None
        
        self.setup_board_state(game, settlements_config)
        self.setup_player_points(game, [2, 5, 3, 4])
        
        move = agent.handle_robber_move(game)
        
        # Should not move to desert if other options exist
        assert move[0] != (0, 0)
        assert move[0] == (1, 1)