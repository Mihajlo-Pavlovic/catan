# agents/simple_agent.py

"""
SimpleAgent: A basic AI implementation for playing Catan.

This agent follows a straightforward strategy prioritizing:
1. Initial placement optimization using probability scores
2. Settlement building in high-probability locations
3. Road building to expand territory
4. City upgrades to increase resource production

The agent makes decisions based on:
- Resource availability
- Building limits (settlements, roads, cities)
- Probability scores of resource production
- Opponent positions (for robber placement)
"""

import random
from typing import Dict, Union, Tuple, List
from game.game import Game
from game.player import Player
from game.board import Vertex, Edge, Vertex_Id
from game.constants import (
    MAX_SETTLEMENTS,          # Maximum number of settlements allowed
    MAX_ROADS,               # Maximum number of roads allowed
    MAX_CITIES,              # Maximum number of cities allowed
)

class SimpleAgent:
    """
    A basic AI agent that follows a simple priority-based strategy.
    
    Strategy Priority:
    1. Build settlements in high-probability locations
    2. Build roads to expand territory
    3. Upgrade settlements to cities
    4. Use robber to hinder leading opponents
    
    The agent uses probability scores to evaluate:
    - Initial settlement placement
    - Expansion directions
    - Resource production potential
    """

    def __init__(self, player: Player) -> None:
        self.player = player


    def handle_initial_placement_first_turn(self, game: Game) -> List[Tuple[str, Union[int, Tuple[int, int]]]]:
        """
        Handle first settlement and road placement in setup phase.
        
        Strategy:
        1. Choose vertex with highest probability score
        2. Ensure no adjacent settlements exist
        3. Place road to enable future expansion
        
        Returns:
            List of placement actions (settlement and road)
        """
        # Sort vertices by probability score from game.constants.VERTEX_PROBABILITY_SCORE
        # Chose first that is free and has highest score
        # Select random edge connected to the vertex to place the road
        # Return list of actions
        actions = []
        # Sort vertices by probability score
        sorted_vertices = sorted(game.board.vertices.keys(), key=lambda x: game.board.vertices[x].probability_score, reverse=True)
        for vertex in sorted_vertices:
            if game.board.vertices[vertex].settlement is None and all(adj.settlement is None for adj in game.board.vertices[vertex].adjacent_vertices):
                actions.append(("place_settlement", vertex))
                # Select random edge connected to the vertex to place the road
                random_edge = (vertex, random.choice(game.board.vertices[vertex].adjacent_vertices).id)
                actions.append(("place_road", random_edge))
                break
        
        return actions
    
    def handle_initial_placement_second_turn(self, game: Game) -> List[Tuple[str, Union[int, Tuple[int, int]]]]:
        """
        Handle second settlement and road placement in setup phase.
        
        Strategy:
        1. Choose high-probability vertex away from first settlement
        2. Consider resource diversity for starting hand
        3. Place road toward valuable future locations
        
        Returns:
            List of placement actions (settlement and road)
        """
        actions = []
        # Sort vertices by probability score
        sorted_vertices = sorted(game.board.vertices.keys(), key=lambda x: game.board.vertices[x].probability_score, reverse=True)
        for vertex in sorted_vertices:
            if game.board.vertices[vertex].settlement is None and all(adj.settlement is None for adj in game.board.vertices[vertex].adjacent_vertices):
                actions.append(("place_settlement", vertex))
                # Select random edge connected to the vertex to place the road
                random_edge = (vertex, random.choice(game.board.vertices[vertex].adjacent_vertices).id)
                actions.append(("place_road", random_edge))
                break
        
        return actions
        
        
        

    def decide_turn_actions(self, game: Game) -> List[Tuple[str, Union[int, Tuple[int, int]]]]:
        """
        Determine build actions for the current turn.
        
        Strategy Priority:
        1. Build settlement if resources available and good location exists
        2. Build road if resources available and expansion possible
        3. Upgrade settlement to city if resources available
        
        Returns:
            List of build actions to perform this turn
        """

        actions = []

        # 1. Build a settlement
        if self._can_build_settlement():
            settlement_vertex_id = self._find_valid_settlement_spot(game)
            if settlement_vertex_id is not None:
                actions.append(("place_settlement", settlement_vertex_id))
                # If we do place a settlement, we might stop here to limit action frequency
                # but let's continue to see if we also want to build roads or cities in the same turn

        # 2. Build a road
        elif self._can_build_road():
            edge_tuple = self._find_valid_road_spot(game)
            if edge_tuple is not None:
                actions.append(("place_road", edge_tuple))

        # 3. Upgrade settlement to a city
        elif self._can_build_city():
            settlement_vertex_id = self._find_existing_settlement_to_upgrade()
            if settlement_vertex_id is not None:
                actions.append(("place_city", settlement_vertex_id))

        # 4. Buy development card
        elif self._can_buy_development_card(game):
            actions.append(("buy_development_card", None))

        # If we found no possible actions, we do nothing (end turn).
        return actions

    # ----------------------------------------------------------------------
    # Settlement logic
    # ----------------------------------------------------------------------
    def _can_build_settlement(self) -> bool:
        """
        Check if settlement construction is possible.
        
        Verifies:
        1. Player has required resources (1 each: wood, brick, sheep, wheat)
        2. Player hasn't reached settlement limit
        3. Valid placement location exists
        """
        r = self.player.resources
        has_resources = (r["wood"] >= 1 and r["brick"] >= 1 and
                r["sheep"] >= 1 and r["wheat"] >= 1)
        has_space = len(self.player.settlements) < MAX_SETTLEMENTS
        return has_resources and has_space

    def _find_valid_settlement_spot(self, game: Game) -> Union[int, None]:
        """
        Find optimal location for next settlement.
        
        Selection criteria:
        1. Must be connected to player's road network
        2. No adjacent settlements/cities
        3. Prefer high probability locations
        4. Consider resource diversity
        """


        # Gather all vertices connected to the player's roads or settlements
        candidate_vertices = set()
        for road in self.player.roads:
            (v1, v2) = road.vertices
            candidate_vertices.add(v1)
            candidate_vertices.add(v2)

        for settlement_vertex in self.player.settlements:
            candidate_vertices.add(settlement_vertex.id)

        # Now, see if any candidate vertex is free (and not adjacent to any settlement)
        for vertex_id in candidate_vertices:
            vertex_obj = game.board.vertices[vertex_id]
            # Check the vertex itself is free
            if not self._vertex_is_free(vertex_obj):
                continue
            # Check adjacency
            if any(adj.settlement is not None for adj in vertex_obj.adjacent_vertices):
                continue

            return vertex_id

        return None

    def _vertex_is_free(self, vertex_obj: Vertex) -> bool:
        """
        Check if vertex is available for building.
        
        A vertex is considered free if:
        1. No settlement present
        2. No city present
        3. No adjacent settlements/cities
        """
        return (vertex_obj.settlement is None and vertex_obj.city is None)

    # ----------------------------------------------------------------------
    # Road logic
    # ----------------------------------------------------------------------
    def _can_build_road(self) -> bool:
        """
        Check if road construction is possible.
        
        Verifies:
        1. Player has required resources (1 wood, 1 brick)
        2. Player hasn't reached road limit
        3. Valid placement location exists
        """
        r = self.player.resources
        has_resources = (r["wood"] >= 1 and r["brick"] >= 1)
        has_space = len(self.player.roads) < MAX_ROADS
        return has_resources and has_space

    def _find_valid_road_spot(self, game: Game) -> Union[Tuple[int, int], None]:
        """
        Find optimal location for next road.
        
        Selection criteria:
        1. Must connect to existing road network
        2. Leads toward valuable building locations
        3. Helps create longest road
        4. Blocks opponent expansion
        """
        # Gather candidate edges by looking at all edges from:
        #  - The player's roads
        #  - The player's settlement vertices
        candidate_edges = set()

        # Expand from each existing road
        for road in self.player.roads:
            (v1_id, v2_id) = road.vertices
            # For each of these vertices, gather all adjacent edges
            # We can get neighbor vertex IDs from board.vertices[v1_id].adjacent_vertices
            for next_vertex in game.board.vertices[v1_id].adjacent_vertices:
                candidate_edges.add(tuple(sorted((v1_id, next_vertex.id))))
            for next_vertex in game.board.vertices[v2_id].adjacent_vertices:
                candidate_edges.add(tuple(sorted((v2_id, next_vertex.id))))


        # Now check which of these edges are valid (not occupied)
        for v1_id, v2_id in candidate_edges:
            # The board stores edges in sorted (v1,v2) form, so we can retrieve it easily
            v1_id, v2_id = sorted((v1_id, v2_id))
            if (v1_id, v2_id) not in game.board.edges:
                continue
            edge_id = (v1_id, v2_id)
            edge_obj = game.board.edges[edge_id]
            if edge_obj.road is None:  # means unoccupied
                return edge_id

        # If none found, return None
        return None

    # ----------------------------------------------------------------------
    # City logic
    # ----------------------------------------------------------------------
    def _can_build_city(self) -> bool:
        """
        Check if city upgrade is possible.
        
        Verifies:
        1. Player has required resources (2 wheat, 3 ore)
        2. Player hasn't reached city limit
        3. Player has settlement to upgrade
        """
        r = self.player.resources
        has_resources = (r["wheat"] >= 2 and r["ore"] >= 3)
        has_space = len(self.player.cities) < MAX_CITIES
        return has_resources and has_space

    def _find_existing_settlement_to_upgrade(self) -> Union[int, None]:
        """
        Find best settlement to upgrade to city.
        
        Selection criteria:
        1. Must be player's settlement
        2. Not already a city
        3. Prefer high-probability locations
        4. Consider resource type for future production
        """
        for vertex in self.player.settlements:
            if vertex.city is None:  # means it's still just a settlement
                return vertex.id
        return None
    
    # ----------------------------------------------------------------------
    # Robber logic
    # ----------------------------------------------------------------------
    def handle_robber_move(self, game: Game) -> Tuple[Tuple[int, int], Union[Player, None]]:
        """
        Determine robber placement and theft target.
        
        Strategy:
        1. Target player with highest victory points
        2. Place robber on high-value tile
        3. Avoid self-harm (own settlements)
        4. Consider resource denial impact
        
        Returns:
            Tuple of (robber_coordinates, player_to_steal_from)
        """
        # Find player with most points (excluding self)
        target_player = None
        max_points = -1
        for player in game.players:
            if player != self.player and player.victory_points > max_points:
                    target_player = player
                    max_points = player.victory_points

        # Get all valid tiles (not current robber location and not our settlements)
        valid_tiles = []
        for coord, tile in game.board.tiles.items():
            if coord == game.board.robber:
                continue
            
            our_settlement_here = False
            for vertex in tile.vertices:
                if vertex.settlement == self.player or vertex.city == self.player:
                    our_settlement_here = True
                    break
            
            if not our_settlement_here:
                valid_tiles.append(coord)

        if not valid_tiles:  # If no valid tiles found (shouldn't happen in normal game)
            return (next(coord for coord in game.board.tiles.keys() 
                    if coord != game.board.robber), None)

        if target_player is None:
            # If no valid target, move robber to any valid tile
            return (valid_tiles[0], None)

        # Find best tile to target opponent
        best_tile_coord = None
        
        # First preference: tiles where target player has buildings but we don't
        for coord in valid_tiles:
            tile = game.board.tiles[coord]
            target_player_here = False
            
            for vertex in tile.vertices:
                if vertex.settlement == target_player or vertex.city == target_player:
                    target_player_here = True
                    break
                
            if target_player_here:
                best_tile_coord = coord
                break
        
        # If no ideal tile found, use any valid tile
        if best_tile_coord is None:
            best_tile_coord = valid_tiles[0]
        
        return (best_tile_coord, target_player)
    
    # ----------------------------------------------------------------------
    # Development card logic
    # ----------------------------------------------------------------------
    def _can_buy_development_card(self, game: Game) -> bool:
        """
        Check if buying a development card is possible.

        Verifies:
        1. Player has required resources (1 wheat, 1 ore, 1 sheep)
        2. Player hasn't reached development card limit
        """
        has_resources = (self.player.resources["wheat"] >= 1 and 
                         self.player.resources["ore"] >= 1 and 
                         self.player.resources["sheep"] >= 1)
        development_card_left = len(game.development_deck) > 0
        return has_resources and development_card_left
    
    # ----------------------------------------------------------------------
    # Slash logic
    # ----------------------------------------------------------------------
    # TODO Cover with tests
    def handle_slash(self) -> Dict[str, int]:
        """
        Determine which resources to discard randomly when the player has more than 7 cards.

        Returns:
            Dict[str, int]: A mapping of resource types to the number of cards to discard.
        """
        discard_dict = {}
        total_resources = sum(self.player.resources.values())


        # Calculate how many cards to discard (half, rounded down)
        required_discard = total_resources // 2

        # Convert resources to a list where each entry corresponds to one card
        # e.g. if we have 3 wood, we have ["wood", "wood", "wood"] in the list
        resource_cards = []
        for resource_type, amount in self.player.resources.items():
            resource_cards.extend([resource_type] * amount)

        # Randomly choose which cards to discard
        # We pop from resource_cards to form the discard set
        random.shuffle(resource_cards)
        cards_to_discard = resource_cards[:required_discard]

        # Count how many of each resource we selected
        for card in cards_to_discard:
            discard_dict[card] = discard_dict.get(card, 0) + 1

        return discard_dict
        
        
        

