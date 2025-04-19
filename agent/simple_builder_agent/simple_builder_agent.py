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
from game.development_cards import DevelopmentCard
from game.game import Game
from game.player import Player
from game.board import Vertex, Edge, Vertex_Id
from game.constants import (
    MAX_SETTLEMENTS,          # Maximum number of settlements allowed
    MAX_ROADS,               # Maximum number of roads allowed
    MAX_CITIES,
    PORT_RESOURCE_VERTEX_IDS_DICT,
    PORT_VERTEX_IDS,              # Maximum number of cities allowed
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
        4. Buy development card if possible
        
        The agent can perform multiple build actions per turn, tracking resource consumption.
        
        Returns:
            List of build actions to perform this turn
        """

        actions = []
        
        # Create a copy of the player's resources to track consumption
        available_resources = self.player.resources.copy()
        
        # Check if we can play a knight (this doesn't consume resources)
        can_play_knight, knight_move_result, player_to_steal_from = self._can_play_knight(game)
        if can_play_knight:
            actions.append(("play_knight", {
                "knight_move_result": knight_move_result,
                "player_to_steal_from": player_to_steal_from
            }))
        
        # Keep track of how many settlements, roads, and cities we've built this turn
        settlements_built = 0
        roads_built = 0
        cities_built = 0
        
        # Continue building as long as we have resources and haven't hit limits
        while True:
            # Check what we can build with our current resources
            can_build_settlement, needed_trades_settlement = self._can_build_settlement_with_resources(available_resources)
            can_build_city, needed_trades_city = self._can_build_city_with_resources(available_resources)
            can_build_road, road_trades = self._can_build_road_with_resources(available_resources)
            can_buy_dev_card, dev_card_trades = self._can_buy_development_card_with_resources(game, available_resources)
            
            # If we can't build anything, break the loop
            if not (can_build_settlement or can_build_city or can_build_road or can_buy_dev_card):
                break
                
            # Prioritize settlements
            if can_build_settlement and settlements_built < 2:  # Limit to 2 settlements per turn
                # Perform any necessary trades
                settlement_vertex_id = self._find_valid_settlement_spot(game)
                if settlement_vertex_id is not None:
                    # Update available resources based on trades
                    for resource_to_give, resource_to_receive, give_rate in needed_trades_settlement:
                        available_resources[resource_to_give] -= give_rate
                        available_resources[resource_to_receive] += 1
                        actions.append(("trade_with_bank", {
                            "resource_type_to_give": resource_to_give,
                            "amount_to_give": give_rate,
                            "resource_type_to_receive": resource_to_receive,
                            "amount_to_receive": 1
                        }))
                    
                    # Update available resources for settlement building
                    available_resources["wood"] -= 1
                    available_resources["brick"] -= 1
                    available_resources["sheep"] -= 1
                    available_resources["wheat"] -= 1
                    
                    actions.append(("place_settlement", settlement_vertex_id))
                    settlements_built += 1
                    continue
            
            # Then try to build a city
            if can_build_city and cities_built < 2:  # Limit to 2 cities per turn
                settlement_vertex_id = self._find_existing_settlement_to_upgrade()
                if settlement_vertex_id is not None:
                    # Update available resources based on trades
                    for resource_to_give, resource_to_receive, give_rate in needed_trades_city:
                        available_resources[resource_to_give] -= give_rate
                        available_resources[resource_to_receive] += 1
                        actions.append(("trade_with_bank", {
                            "resource_type_to_give": resource_to_give,
                            "amount_to_give": give_rate,
                            "resource_type_to_receive": resource_to_receive,
                            "amount_to_receive": 1
                        }))
                    
                    # Update available resources for city building
                    available_resources["wheat"] -= 2
                    available_resources["ore"] -= 3
                    
                    actions.append(("place_city", settlement_vertex_id))
                    cities_built += 1
                    continue
            
            # Then try to build a road
            if can_build_road and roads_built < 3:  # Limit to 3 roads per turn
                # Update available resources based on trades
                for resource_to_give, resource_to_receive, give_rate in road_trades:
                    available_resources[resource_to_give] -= give_rate
                    available_resources[resource_to_receive] += 1
                    actions.append(("trade_with_bank", {
                        "resource_type_to_give": resource_to_give,
                        "amount_to_give": give_rate,
                        "resource_type_to_receive": resource_to_receive,
                        "amount_to_receive": 1
                    }))
                
                # Update available resources for road building
                available_resources["wood"] -= 1
                available_resources["brick"] -= 1
                
                # Then build the road
                edge = self._find_valid_road_spot(game)
                if edge is not None:
                    actions.append(("place_road", edge))
                    roads_built += 1
                    continue
            
            # Finally, try to buy a development card
            if can_buy_dev_card:
                # Update available resources based on trades
                for resource_to_give, resource_to_receive, trade_rate in dev_card_trades:
                    available_resources[resource_to_give] -= trade_rate
                    available_resources[resource_to_receive] += 1
                    actions.append(("trade_with_bank", {
                        "resource_type_to_give": resource_to_give,
                        "amount_to_give": trade_rate,
                        "resource_type_to_receive": resource_to_receive,
                        "amount_to_receive": 1
                    }))
                
                # Update available resources for development card
                available_resources["wheat"] -= 1
                available_resources["ore"] -= 1
                available_resources["sheep"] -= 1
                
                # Then buy the development card
                actions.append(("buy_development_card", None))
                break  # Only buy one development card per turn
        
        # If we found no possible actions, we do nothing (end turn).
        return actions
        
    def _can_build_settlement_with_resources(self, available_resources: Dict[str, int]) -> tuple[bool, list[tuple[str, str, int]]]:
        """
        Check if settlement construction is possible with the given resources and determine necessary trades.
        
        Similar to _can_build_settlement but uses the provided available_resources instead of player.resources.
        
        Returns:
            tuple[bool, list[tuple[str, str, int]]]: 
                - bool: True if settlement can be built
                - list of tuples (resource_to_give, resource_to_receive, rate) for necessary trades
        """
        # Check settlement limit first
        if len(self.player.settlements) >= MAX_SETTLEMENTS:
            return False, []

        # Check if has direct resources
        required_resources = {"wood": 1, "brick": 1, "sheep": 1, "wheat": 1}
        has_resources = all(available_resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive, rate) tuples
        
        for res, amt in required_resources.items():
            if available_resources[res] < amt:
                # Need this resource
                needed_resources[res] = amt - available_resources[res]
            else:
                # Have enough of this resource, mark it as used
                available_resources[res] -= amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    if available_resources[give_res] >= give_rate:
                        # Can make this trade
                        available_resources[give_res] -= give_rate
                        needed_resources[needed_res] -= 1
                        needed_amt -= 1
                        trades_to_make.append((give_res, needed_res, give_rate))
                        best_trade_found = True
                        break
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_build = all(amt <= 0 for amt in needed_resources.values())
        return can_build, trades_to_make
        
    def _can_build_road_with_resources(self, available_resources: Dict[str, int]) -> tuple[bool, list[tuple[str, str, int]]]:
        """
        Check if road construction is possible with the given resources and determine necessary trades.
        
        Similar to _can_build_road but uses the provided available_resources instead of player.resources.
        
        Returns:
            tuple[bool, list[tuple[str, str, int]]]: 
                - bool: True if road can be built
                - list of tuples (resource_to_give, resource_to_receive, rate) for necessary trades
        """
        # Check road limit first
        if len(self.player.roads) >= MAX_ROADS:
            return False, []

        # Check if has direct resources
        required_resources = {"wood": 1, "brick": 1}
        has_resources = all(available_resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive, rate) tuples
        
        # First, account for resources we already have
        for res, amt in required_resources.items():
            if available_resources[res] < amt:
                # Only add to needed_resources if we actually need more
                needed_resources[res] = max(amt - available_resources[res], 0)
            else:
                # If we have enough, just mark it as used and don't add to needed_resources
                available_resources[res] -= amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    # Skip if this is a resource we need
                    if give_res in needed_resources:
                        continue
                    # Skip if we don't have enough of this resource to trade
                    if available_resources[give_res] < give_rate:
                        continue
                    
                    # Can make this trade
                    available_resources[give_res] -= give_rate
                    needed_resources[needed_res] -= 1
                    needed_amt -= 1
                    trades_to_make.append((give_res, needed_res, give_rate))
                    best_trade_found = True
                    break
                    
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_build = all(amt <= 0 for amt in needed_resources.values())
        return can_build, trades_to_make
    
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


        
    def _can_build_city_with_resources(self, available_resources: Dict[str, int]) -> tuple[bool, list[tuple[str, str, int]]]:
        """
        Check if city upgrade is possible with the given resources and determine necessary trades.
        
        Similar to _can_build_city but uses the provided available_resources instead of player.resources.
        
        Returns:
            tuple[bool, list[tuple[str, str, int]]]: 
                - bool: True if city can be built
                - list of tuples (resource_to_give, resource_to_receive, rate) for necessary trades
        """
        # Check city limit first
        if len(self.player.cities) >= MAX_CITIES:
            return False, []

        # Check if has direct resources
        required_resources = {"wheat": 2, "ore": 3}
        has_resources = all(available_resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {'ore': 3, 'wheat': 2}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive, rate) tuples
        
        # First, account for resources we already have
        for res, amt in required_resources.items():
            if available_resources[res] < amt:
                # Only add to needed_resources if we actually need more
                needed_resources[res] = amt - available_resources[res]
                # Reduce available amount of this resource as we'll use what we have
                available_resources[res] = 0
            else:
                # If we have enough, just mark it as used and don't add to needed_resources
                available_resources[res] -= amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    # Skip if this is a resource we need
                    if give_res in needed_resources:
                        continue
                    # Skip if we don't have enough of this resource to trade
                    if available_resources[give_res] < give_rate:
                        continue
                    
                    # Can make this trade
                    available_resources[give_res] -= give_rate
                    needed_resources[needed_res] -= 1
                    needed_amt -= 1
                    trades_to_make.append((give_res, needed_res, give_rate))
                    best_trade_found = True
                    break
                    
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_build = all(amt <= 0 for amt in needed_resources.values())
        return can_build, trades_to_make
        
    def _can_buy_development_card_with_resources(self, game: Game, available_resources: Dict[str, int]) -> tuple[bool, list[tuple[str, str, int]]]:
        """
        Check if buying a development card is possible with the given resources and determine necessary trades.
        
        Similar to _can_buy_development_card but uses the provided available_resources instead of player.resources.
        
        Returns:
            tuple[bool, list[tuple[str, str, int]]]: 
                - bool: True if development card can be bought
                - list of tuples (resource_to_give, resource_to_receive, rate) for necessary trades
        """
        # Check if there are development cards left
        if len(game.development_deck) == 0:
            return False, []

        # Check if has direct resources
        required_resources = {"wheat": 1, "ore": 1, "sheep": 1}
        has_resources = all(available_resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive, rate) tuples
        
        # First, account for resources we already have
        for res, amt in required_resources.items():
            if available_resources[res] < amt:
                # Only add to needed_resources if we actually need more
                needed_resources[res] = max(amt - available_resources[res], 0)
            else:
                # If we have enough, just mark it as used and don't add to needed_resources
                available_resources[res] -= amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    # Skip if this is a resource we need
                    if give_res in needed_resources:
                        continue
                    # Skip if we don't have enough of this resource to trade
                    if available_resources[give_res] < give_rate:
                        continue
                    
                    # Can make this trade
                    available_resources[give_res] -= give_rate
                    needed_resources[needed_res] -= 1
                    needed_amt -= 1
                    trades_to_make.append((give_res, needed_res, give_rate))
                    best_trade_found = True
                    break
                    
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_buy = all(amt <= 0 for amt in needed_resources.values())
        return can_buy, trades_to_make

    # ----------------------------------------------------------------------
    # Settlement logic
    # ----------------------------------------------------------------------

    def _can_build_settlement(self) -> tuple[bool, list[tuple[str, str]]]:
        """
        Check if settlement construction is possible and determine necessary trades.
        
        Verifies:
        1. Player has required resources (1 each: wood, brick, sheep, wheat)
        2. Player hasn't reached settlement limit
        3. Resources can be obtained through trading if not directly available
        
        Returns:
            tuple[bool, list[tuple[str, str]]]: 
                - bool: True if settlement can be built
                - list of tuples (resource_to_give, resource_to_receive) for necessary trades
        """
        # Check settlement limit first
        if len(self.player.settlements) >= MAX_SETTLEMENTS:
            return False, []

        # Check if has direct resources
        required_resources = {"wood": 1, "brick": 1, "sheep": 1, "wheat": 1}
        has_resources = all(self.player.resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        available_resources = self.player.resources.copy()
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive) tuples
        
        for res, amt in required_resources.items():
            if self.player.resources[res] < amt:
                # Need this resource
                needed_resources[res] = amt - self.player.resources[res]
            else:
                # Have enough of this resource, mark it as used
                available_resources[res] -= amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    if available_resources[give_res] >= give_rate:
                        # Can make this trade
                        available_resources[give_res] -= give_rate
                        needed_resources[needed_res] -= 1
                        needed_amt -= 1
                        trades_to_make.append((give_res, needed_res, give_rate))
                        best_trade_found = True
                        break
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_build = all(amt <= 0 for amt in needed_resources.values())
        return can_build, trades_to_make

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
    def _can_build_road(self) -> tuple[bool, list[tuple[str, str, int]]]:
        """
        Check if road construction is possible and determine necessary trades.
        
        Verifies:
        1. Player has required resources (1 wood, 1 brick)
        2. Player hasn't reached road limit
        3. Resources can be obtained through using development card year of plenty
        4. Resources can be obtained through trading if not directly available
        
        Returns:
            tuple[bool, list[tuple[str, str, int]]]: 
                - bool: True if road can be built
                - list of tuples (resource_to_give, resource_to_receive, rate) for necessary trades
        """
        # Check road limit first
        if len(self.player.roads) >= MAX_ROADS:
            return False, []

        # Check if has direct resources
        required_resources = {"wood": 1, "brick": 1}
        has_resources = all(self.player.resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        available_resources = self.player.resources.copy()
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive, rate) tuples
        
        # First, account for resources we already have
        for res, amt in required_resources.items():
            if self.player.resources[res] < amt:
                # Only add to needed_resources if we actually need more
                needed_resources[res] = max(amt - self.player.resources[res], 0)
            else:
                # If we have enough, just mark it as used and don't add to needed_resources
                available_resources[res] = self.player.resources[res] - amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    # Skip if this is a resource we need
                    if give_res in needed_resources:
                        continue
                    # Skip if we don't have enough of this resource to trade
                    if available_resources[give_res] < give_rate:
                        continue
                    
                    # Can make this trade
                    available_resources[give_res] -= give_rate
                    needed_resources[needed_res] -= 1
                    needed_amt -= 1
                    trades_to_make.append((give_res, needed_res, give_rate))
                    best_trade_found = True
                    break
                    
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_build = all(amt <= 0 for amt in needed_resources.values())
        return can_build, trades_to_make

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
    def _can_build_city(self) -> tuple[bool, list[tuple[str, str]]]:
        """
        Check if city upgrade is possible and determine necessary trades.
        
        Verifies:
        1. Player has required resources (2 wheat, 3 ore)
        2. Player hasn't reached city limit
        3. Resources can be obtained through trading if not directly available
        
        Returns:
            tuple[bool, list[tuple[str, str]]]: 
                - bool: True if city can be built
                - list of tuples (resource_to_give, resource_to_receive) for necessary trades
        """
        # Check city limit first
        if len(self.player.cities) >= MAX_CITIES:
            return False, []

        # Check if has direct resources
        required_resources = {"wheat": 2, "ore": 3}
        has_resources = all(self.player.resources[res] >= amt 
                           for res, amt in required_resources.items())
        if has_resources:
            return True, []

        # If direct resources not available, check trading possibilities
        available_resources = self.player.resources.copy()
        # Get available trade rates for each port the player has access to
        trade_rates = {"wood": 4, "brick": 4, "sheep": 4, "wheat": 4, "ore": 4}  # Default 4:1
        for settlement in self.player.settlements:
            if settlement.id in PORT_VERTEX_IDS:
                port_type = PORT_VERTEX_IDS[settlement.id]
                if port_type == 'any':
                    # 3:1 port - update all rates that are worse than 3
                    for resource in trade_rates:
                        trade_rates[resource] = min(trade_rates[resource], 3)
                else:
                    # 2:1 port for specific resource
                    trade_rates[port_type] = 2

        # Calculate needed resources and update available resources
        needed_resources = {'ore': 3, 'wheat': 2}
        trades_to_make = []  # List of (resource_to_give, resource_to_receive) tuples
        
        # First, account for resources we already have
        for res, amt in required_resources.items():
            if self.player.resources[res] < amt:
                # Only add to needed_resources if we actually need more
                needed_resources[res] = amt - self.player.resources[res]
                # Reduce available amount of this resource as we'll use what we have
                available_resources[res] = 0
            else:
                # If we have enough, just mark it as used and don't add to needed_resources
                available_resources[res] = self.player.resources[res] - amt

        # Try to satisfy each needed resource through trading
        for needed_res, needed_amt in needed_resources.items():
            while needed_amt > 0:
                best_trade_found = False
                # Find the best resource to trade with (lowest trade rate)
                for give_res, give_rate in sorted(trade_rates.items(), key=lambda x: x[1]):
                    # Skip if this is a resource we need
                    if give_res in needed_resources:
                        continue
                    # Skip if we don't have enough of this resource to trade
                    if available_resources[give_res] < give_rate:
                        continue
                    
                    # Can make this trade
                    available_resources[give_res] -= give_rate
                    needed_resources[needed_res] -= 1
                    needed_amt -= 1
                    trades_to_make.append((give_res, needed_res, give_rate))
                    best_trade_found = True
                    break
                    
                if not best_trade_found:
                    # If we couldn't find any resource to trade for this need
                    return False, []

        # If we got here and trades_to_make is not empty, we can build through trading
        can_build = all(amt <= 0 for amt in needed_resources.values())
        return can_build, trades_to_make

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
        1. Target player with highest victory points who has resources
        2. Place robber on highest-value tile (based on probability and resource type)
        3. Avoid self-harm (own settlements)
        4. Consider both settlements and cities (cities are higher value targets)
        5. Ensure target player has resources to steal
        
        Returns:
            Tuple of (robber_coordinates, player_to_steal_from)
        """
        # Score each player as a potential target
        player_scores = {}
        for player in game.players:
            if player == self.player or sum(player.resources.values()) == 0:
                continue
            
            # Base score is victory points
            score = player.victory_points * 2
            
            # Bonus for having lots of resources
            score += min(sum(player.resources.values()), 7) // 2
            
            # Bonus for having largest army or longest road
            if player.victory_points > len(player.settlements) + len(player.cities):
                score += 2
            
            player_scores[player] = score
        
        if not player_scores:
            # No valid targets with resources, just move robber away from our buildings
            valid_coords = []
            for coord, tile in game.board.tiles.items():
                if coord == game.board.robber or tile.resource_type == "desert":
                    continue
                if not any(v.settlement == self.player or v.city == self.player 
                          for v in tile.vertices):
                    valid_coords.append(coord)
            return (valid_coords[0] if valid_coords else next(
                coord for coord, tile in game.board.tiles.items() 
                if coord != game.board.robber), None)
        
        # Get target player with highest score
        target_player = max(player_scores.items(), key=lambda x: x[1])[0]
        
        # Score each tile based on multiple factors
        tile_scores = {}
        # Track players with buildings on each tile for later reference
        tile_players = {}  # coord -> list of players with buildings
        
        for coord, tile in game.board.tiles.items():
            if coord == game.board.robber or tile.resource_type == "desert":
                continue
            
            # Skip if we have buildings here
            if any(v.settlement == self.player or v.city == self.player 
                   for v in tile.vertices):
                continue
            
            # Base score from probability
            prob_score = {
                2: 1, 12: 1,
                3: 2, 11: 2,
                4: 3, 10: 3,
                5: 4, 9: 4,
                6: 5, 8: 5
            }.get(tile.number, 0)
            
            # Resource value score
            resource_score = {
                "ore": 5,    # Cities need ore
                "wheat": 4,  # Cities and dev cards need wheat
                "sheep": 3,  # Dev cards need sheep
                "brick": 2,  # Early game roads/settlements
                "wood": 1    # Early game roads/settlements
            }.get(tile.resource_type, 0)
            
            score = prob_score * resource_score
            
            # Track all players with buildings on this tile
            players_here = set()
            target_buildings = 0
            other_players_buildings = 0
            
            for vertex in tile.vertices:
                if vertex.settlement is not None:
                    player = vertex.settlement
                    if player != self.player:
                        players_here.add(player)
                        if player == target_player:
                            target_buildings += 1
                        else:
                            other_players_buildings += 1
                if vertex.city is not None:
                    player = vertex.city
                    if player != self.player:
                        players_here.add(player)
                        if player == target_player:
                            target_buildings += 2  # Cities count double
                        else:
                            other_players_buildings += 2
            
            # Only consider tiles where at least one player has resources
            if not any(sum(p.resources.values()) > 0 for p in players_here):
                continue
            
            # Bonus for targeting our chosen player
            score *= (1 + target_buildings)
            
            # Small bonus for hitting other players too
            score *= (1 + other_players_buildings * 0.2)
            
            tile_scores[coord] = score
            tile_players[coord] = players_here
        
        if not tile_scores:
            # No ideal tiles, find any valid tile
            valid_coords = [coord for coord, tile in game.board.tiles.items()
                           if coord != game.board.robber and tile.resource_type != "desert"]
            return (valid_coords[0], None)
        
        # Get best scoring tile
        best_tile = max(tile_scores.items(), key=lambda x: x[1])[0]
        
        # Verify target player has buildings on chosen tile and has resources
        tile = game.board.tiles[best_tile]
        if not any((v.settlement == target_player or v.city == target_player) 
                   for v in tile.vertices) or sum(target_player.resources.values()) == 0:
            # Find new target player who has buildings here AND resources
            players_on_tile = tile_players[best_tile]
            potential_targets = [p for p in players_on_tile 
                               if sum(p.resources.values()) > 0]
            
            if potential_targets:
                # Choose the player with the most victory points among those with resources
                target_player = max(potential_targets, 
                                  key=lambda p: p.victory_points)
            else:
                # No players with resources on this tile
                target_player = None
                
        return (best_tile, target_player)
    
    # ----------------------------------------------------------------------
    # Development card logic
    # ----------------------------------------------------------------------
    def _can_play_knight(self, game: Game) -> tuple[bool, tuple[int, int], Player]:
        """
        Check if playing a knight development card is possible.

        Verifies:
        1. Player has a knight development card
        2. Player is blocked by a robber

        Returns:
            tuple[bool, tuple[int, int]]:
                - bool: True if knight can be played
                - tuple[int, int]: coordinates of the tile to move the robber to
                - Player: player to steal from
        """
        # Check if player has a knight development card
        if self.player.development_cards[DevelopmentCard.KNIGHT] == 0:
            return False, None, None
        
        # Check if player is blocked by a robber
        # blocked_by_robber = False
        # robber_tile = game.board.tiles[game.board.robber]
        # for vertex in robber_tile.vertices:
        #     if vertex.settlement == self.player or vertex.city == self.player:
        #         blocked_by_robber = True
        #         break
        
        # if not blocked_by_robber:
        #     return False, None, None
        
        robber_move_result = self.handle_robber_move(game)
        if robber_move_result[0] is None:
            return False, None
        
        return True, robber_move_result[0], robber_move_result[1]

