#game/game.py
import random
from game.constants import ANY, MAX_SETTLEMENTS, MAX_CITIES, MAX_ROADS, PORT_RESOURCE_VERTEX_IDS_DICT, RESOURCE_TYPES
from game.board import Board, Edge, Vertex
from game.player import Player
from game.development_cards import DevelopmentCard


class Game:
    """
    Represents the main Catan game controller.
    
    This class manages the game state, including the board, players, and all game actions.
    It enforces game rules and manages resource transactions.
    
    Attributes:
        board (Board): The game board instance
        players (list[Player]): List of players in the game
    """
    def __init__(self, players: list[Player]):
        """
        Initialize a new game.

        Args:
            players (list[Player]): List of players participating in the game
        """
        self.board = Board()
        self.players = players
        self.longest_road = 0
        self.longest_road_player = None
        self.development_deck = self._create_development_deck()


    #def setup(self):
        #for player in self.players:

    def _create_development_deck(self):
        deck = (
            [DevelopmentCard.KNIGHT] * 14 +
            [DevelopmentCard.VICTORY_POINT] * 5 +
            [DevelopmentCard.ROAD_BUILDING] * 2 +
            [DevelopmentCard.YEAR_OF_PLENTY] * 2 +
            [DevelopmentCard.MONOPOLY] * 2
        )
        random.shuffle(deck)
        return deck


    def _place_settlement(self, player: Player, vertex: Vertex, initial_placement: bool = False):
        """
        Place a settlement for a player at the specified vertex.
        
        This method enforces the following rules:
        - The vertex must exist on the board
        - The vertex must not be already occupied
        - The player must not have settlements on adjacent vertices
        - The player must not exceed maximum settlements
        - The player must have required resources (1 wood, 1 brick, 1 sheep, 1 wheat)
        
        Args:
            player (Player): The player placing the settlement
            vertex (Vertex): The vertex where the settlement will be placed
            
        Raises:
            AssertionError: If the vertex doesn't exist on the board
            ValueError: If placement violates any game rules
        """
        assert vertex.id in self.board.vertices.keys(), f"Vertex {vertex} does not exist on the board"
        # Check if vertex is already occupied
        if vertex.settlement is not None:
          raise ValueError("Vertex already has a settlement")
      # For each adjacent vertex check if there is a settlement, if yes, raise an error
        for adjacent_vertex in vertex.adjacent_vertices:
          if adjacent_vertex.settlement is not None:
            raise ValueError("There is settlement on adjacent vertex")
        # Check if player has enough resources
        if len(player.settlements) >= MAX_SETTLEMENTS:
          raise ValueError("Player has too many settlements")
        if not initial_placement:
          if player.resources["wood"] < 1 or player.resources["brick"] < 1 or player.resources["sheep"] < 1 or player.resources["wheat"] < 1:
            raise ValueError("Player does not have enough resources to place a settlement")
        # Place settlement
        vertex.settlement = player
        player.settlements.append(vertex)
        # Remove resources from player
        if not initial_placement:
          player.resources["wood"] -= 1
          player.resources["brick"] -= 1
          player.resources["sheep"] -= 1
          player.resources["wheat"] -= 1
        player.victory_points += 1


        for player in self.players:
            self._update_longest_road(player)

    def _place_road(self, player: Player, edge: Edge, initial_placement: bool = False):
        """
        Place a road for a player at the specified edge.
            
        Enforces:
        - The edge must exist on the board.
        - The edge must not already have a road.
        - Must have correct resources (1 wood, 1 brick) if not in initial placement.
        - Must not exceed maximum roads.
        - (Optional) For non-initial placements, the edge must connect to at least one vertex 
          that is occupied by the player's settlement/city or touches another of that player's roads.
        After placing the road, update 'longest road' if needed.
        """
        # 1. Basic checks
        assert edge.vertices in self.board.edges, f"Edge {edge} does not exist on the board."
        if edge.road is not None:
            raise ValueError("Edge already has a road.")
        if len(player.roads) >= MAX_ROADS:
            raise ValueError("Player has too many roads.")
        
        # 2. Resource checks (if not initial placement)
        if not initial_placement:
            if player.resources["wood"] < 1 or player.resources["brick"] < 1:
                raise ValueError("Not enough resources to place a road.")
        
        # 3. Connectivity checks (optional but recommended for full rules)
        #    A newly placed road must be adjacent to:
        #    - The player's existing road(s), OR
        #    - A player's settlement/city (which itself is connected to roads).
        #    You can skip this if you rely on the agent to only propose valid edges.
        if not self._road_is_connected(player, edge):
            raise ValueError("Road must connect to the player's existing roads or settlements.")
        
        # 4. Place the road
        edge.road = player
        player.roads.append(edge)
        
        # 5. Pay the resources
        if not initial_placement:
            player.resources["wood"] -= 1
            player.resources["brick"] -= 1
        
        # 6. Update longest road
        self._update_longest_road(player)


    def _road_is_connected(self, player: Player, edge: Edge) -> bool:
        """
        Return True if this 'edge' shares a vertex with either:
          - An existing road belonging to the same player
          - Or a settlement/city of that player.
        This ensures the newly placed road is continuous with the player's network.
        """
        (v1_id, v2_id) = edge.vertices
        v1 = self.board.vertices[v1_id]
        v2 = self.board.vertices[v2_id]
        
        # Check if either v1 or v2 is occupied by player's settlement or city
        # Or belongs to an existing road.
        # (When checking roads, we see if v1 or v2 is also an endpoint in the player's roads.)
        
        # Settlement/city check:
        if (v1.settlement == player) or (v2.settlement == player):
            return True

        # Road adjacency check:
        for existing_road in player.roads:
            (r1_id, r2_id) = existing_road.vertices
            # If the new road shares a vertex with an existing road, it's connected
            if r1_id == v1_id or r1_id == v2_id or r2_id == v1_id or r2_id == v2_id:
                return True

        return False


    def _update_longest_road(self, player: Player):
        """
        Recalculate the longest road length for 'player' and update game state if it exceeds the current record.
        Always tracks the longest road length, but only awards victory points for 5 or more segments.
        """
        longest_road_length = self._calculate_player_longest_road(player)
        
        print(self.longest_road, self.longest_road_player)
        if longest_road_length > self.longest_road:
          self.longest_road = longest_road_length
          if longest_road_length >= 5:
            player.victory_points += 2
            if self.longest_road_player is not None:
              self.longest_road_player.victory_points -= 2
            self.longest_road_player = player
        elif player is self.longest_road_player and longest_road_length < self.longest_road:
          if longest_road_length < 5:
            player.victory_points -= 2
            self.longest_road_player = None
          self.longest_road = longest_road_length


    def _calculate_player_longest_road(self, player: Player) -> int:
        """
        Returns the length of the longest continuous road (path) owned by 'player'.
        For each road edge, we consider it an undirected connection between the two vertices.
        We'll do a DFS for each possible starting vertex, tracking used edges to avoid reuse.
        Opponent settlements act as breaking points, creating separate road segments.
        """
        from collections import defaultdict
        
        # 1. Build adjacency map of the player's road network:
        #    adjacency[vertex_id] = list of connected vertex_ids via roads
        adjacency = defaultdict(list)
        for edge in player.roads:
            (v1_id, v2_id) = edge.vertices
            adjacency[v1_id].append(v2_id)
            adjacency[v2_id].append(v1_id)
        
        # 2. DFS to find the longest path, stopping at opponent settlements
        def dfs(current_vertex_id, visited_edges, visited_vertices):
            # Stop if we hit an opponent's settlement (but count the path up to here)
            if (current_vertex_id in visited_vertices or
                (self.board.vertices[current_vertex_id].settlement is not None and 
                 self.board.vertices[current_vertex_id].settlement != player and 
                 current_vertex_id != start_vertex)):  # Allow starting from opponent settlement
                return 0
            
            visited_vertices.add(current_vertex_id)
            max_length = 0
            
            # Explore neighbors
            for neighbor_id in adjacency[current_vertex_id]:
                edge_tuple = tuple(sorted((current_vertex_id, neighbor_id)))
                if edge_tuple not in visited_edges:
                    visited_edges.add(edge_tuple)
                    length = 1 + dfs(neighbor_id, visited_edges, visited_vertices)
                    if length > max_length:
                        max_length = length
                    visited_edges.remove(edge_tuple)
            
            visited_vertices.remove(current_vertex_id)
            return max_length
        
        # 3. Try DFS from each vertex in adjacency to find a global maximum
        global_max = 0
        for start_vertex in adjacency:
            # Each DFS has its own visited-edges and visited-vertices sets
            path_length = dfs(start_vertex, set(), set())
            global_max = max(global_max, path_length)
        
        return global_max

    def _place_city(self, player: Player, vertex: Vertex):
        """
        Upgrade a settlement to a city for a player at the specified vertex.
        
        This method enforces the following rules:
        - The vertex must exist on the board
        - The vertex must have the player's settlement
        - The vertex must not already have a city
        - The player must have required resources (2 wheat, 3 ore)
        - The player must not exceed maximum cities
        
        Args:
            player (Player): The player placing the city
            vertex_id (Vertex_Id): The vertex where the city will be placed
            
        Raises:
            AssertionError: If the vertex doesn't exist on the board
            ValueError: If placement violates any game rules
        """
        assert vertex.id in self.board.vertices, f"Vertex {vertex} does not exist on the board"
        # Check if vertex is already occupied
        if vertex.settlement != player:
          raise ValueError("Vertex does not have player's settlement")
        if vertex.city is not None:
          raise ValueError("Vertex already has a city")
        # Check if player has enough resources
        if player.resources["wheat"] < 2 or player.resources["ore"] < 3:
          raise ValueError("Player does not have enough resources to place a city")
        # Check if player has enough cities
        if len(player.cities) >= MAX_CITIES:
          raise ValueError("Player has too many cities")
        # Place city
        vertex.city = player
        player.cities.append(vertex)
        # Remove resources from player
        player.resources["wheat"] -= 2
        player.resources["ore"] -= 3
        player.victory_points += 1


    def _buy_development_card(self, player: Player):
        """
        Buy a development card for a player.
        
        The cost of a development card is:
        - 1 ore
        - 1 wheat
        - 1 sheep
        
        Args:
            player (Player): The player buying the development card
            
        Raises:
            AssertionError: If there are no development cards left in the deck
            AssertionError: If the player doesn't have enough resources
        """
        # Check if there are any development cards left to buy
        assert len(self.development_deck) > 0, "No development cards left"
        
        # Verify player has the required resources (1 each of ore, wheat, and sheep)
        assert player.resources["ore"] >= 1 and player.resources["wheat"] >= 1 and player.resources["sheep"] >= 1, "Player does not have enough resources to buy a development card"
        
        # Draw the top card from the development card deck
        development_card = self.development_deck.pop()
        
        # Deduct the required resources from the player
        player.resources["ore"] -= 1
        player.resources["wheat"] -= 1
        player.resources["sheep"] -= 1
        
        # Add the development card to the player's hand
        player.development_cards[development_card] += 1

    def _get_resource_from_vertex(self, vertex: Vertex):
        """
        Get the resource type from a vertex.
        
        This method returns the resource type of the tile that the vertex is on.
        Args:
            vertex_id (Vertex_Id): The vertex to get the resource type from
            
        Returns:
            list[str]: A list of resource types

        Raises:
            AssertionError: If the vertex doesn't exist on the board
        """
        return [tile.resource_type for tile in vertex.adjacent_tiles]
    
    
    def _distribute_initial_resources(self):
      """
      Distribute initial resources to each player.
      """
      for player in self.players:
        for vertex in player.settlements:
          for resource_type in self._get_resource_from_vertex(vertex):
            if resource_type != "desert":
              player.resources[resource_type] += 1

    def _distribute_resources(self, dice_roll: int):
        """
        Distribute resources to the players based on the dice roll.
        
        For each tile matching the dice roll:
        - Skip if robber is on the tile
        - Give 1 resource to players with settlements on the tile's vertices
        - Give 2 resources to players with cities on the tile's vertices

        Args:
            dice_roll (int): The dice roll to distribute resources for (2-12)
        """
        tilesThatCanGiveResource = self.board.number_tile_dict[dice_roll]
        for tile in tilesThatCanGiveResource:
          if tile.cord == self.board.robber:
            continue
          for player in self.players:
            for vertex in tile.vertices:
              if vertex in player.settlements:
                player.resources[tile.resource_type] += 1
            for vertex in tile.vertices:
              if vertex in player.cities:
                player.resources[tile.resource_type] += 1
    
    def _roll_dice(self):
      """
      Dice can be any number between 2 and 12
      """
      dice_1 = random.randint(1, 6)
      dice_2 = random.randint(1, 6)
      return dice_1 + dice_2
    
    def _move_robber(self, tile_cord: tuple[int, int]):
      """
      Move the robber to the specified tile.

      Args:
        tile_cord (tuple[int, int]): The tile to move the robber to

      Raises:
        ValueError: If the robber is already on the tile
      """
      if tile_cord == self.board.robber:
        raise ValueError("Robber is already on this tile")
      self.board.robber = tile_cord

    def _who_to_slash(self) -> list[Player]:
        """
        Determine which players must discard half their resources when a 7 is rolled.
        
        According to Catan rules:
        - When a 7 is rolled, any player with more than 7 cards must discard half
        - The number of cards to discard is rounded down
        - Players choose which cards to discard
        
        Returns:
            list[Player]: List of players who have more than 7 resource cards
        
        Example:
            If a player has 9 resources, they must discard 4 resources (9/2 rounded down)
            If a player has 7 or fewer resources, they keep all their cards
        """
        players_to_slash = []
        for player in self.players:
            # Calculate total number of resource cards for this player
            player_resource_sum = sum(player.resources.values())
            
            # If player has more than 7 cards, they must discard
            if player_resource_sum > 7:
                players_to_slash.append(player)
                
        return players_to_slash
    
    def _steal_resource(self, playerThatSteals: Player, playerThatLosesResource: Player):
      """
      Steal a random resource from a player.

      Args:
        playerThatSteals (Player): The player that will steal the resource
        playerThatLosesResource (Player): The player that will lose the resource

      Raises:
        ValueError: If the player that steals is the same as the player that loses the resource
      """
      if playerThatSteals == playerThatLosesResource:
        raise ValueError("Cannot steal from yourself")
      # Find playerThatLosesResource resource that are not 0
      resourcesThatCanBeStolen = [resource for resource in playerThatLosesResource.resources if playerThatLosesResource.resources[resource] > 0]
      assert len(resourcesThatCanBeStolen) > 0, "No resources to steal"
      resourceToSteal = random.choice(resourcesThatCanBeStolen)
      playerThatSteals.resources[resourceToSteal] += 1
      playerThatLosesResource.resources[resourceToSteal] -= 1

    def _trade_with_bank(self, player: Player, resource_type_to_receive: str, amount_to_receive: int, 
                         resource_type_to_give: str, amount_to_give: int):
        """
        Trade resources with the bank at standard (4:1) or port rates (3:1 or 2:1).
        
        Trading rules:
        - Standard rate is 4:1 (give 4 of one resource to receive 1 of another)
        - Port rates can be 3:1 (any resource) or 2:1 (specific resource)
        - Player must have a settlement/city on a port to use its trade rate
        - Player must have enough resources for the trade
        
        Args:
            player (Player): The player making the trade
            resource_type_to_receive (str): The type of resource to receive from bank
            amount_to_receive (int): The amount of resource to receive
            resource_type_to_give (str): The type of resource to give to bank
            amount_to_give (int): The amount of resource to give
            
        Raises:
            AssertionError: If resource types are invalid or amounts are not positive
            ValueError: If player doesn't have enough resources for the trade
        """
        # Validate resource types and amounts
        print(f"resource_type_to_receive: {resource_type_to_receive}, amount_to_receive: {amount_to_receive}, resource_type_to_give: {resource_type_to_give}, amount_to_give: {amount_to_give}")
        assert resource_type_to_receive in RESOURCE_TYPES, f"Invalid resource type to receive: {resource_type_to_receive}"
        assert resource_type_to_give in RESOURCE_TYPES, f"Invalid resource type to give: {resource_type_to_give}"
        assert amount_to_receive > 0, "Amount to receive must be greater than 0"
        assert amount_to_give > 0, "Amount to give must be greater than 0"

        # Determine best available trade rate
        trade_rate = 4  # Standard rate
        for settlement in player.settlements:
            # Check for 2:1 port for specific resource
            if settlement.id in PORT_RESOURCE_VERTEX_IDS_DICT[resource_type_to_give]:
                trade_rate = 2
                break
            # Check for 3:1 port (any resource)
            elif settlement.id in PORT_RESOURCE_VERTEX_IDS_DICT[ANY]:
                trade_rate = 3

        assert trade_rate in [2, 3, 4], "Invalid trade rate"
        assert amount_to_give == trade_rate, "Amount to give must be equal to the trade rate"
        # Calculate total cost
        total_cost = amount_to_receive * trade_rate

        # Verify player has enough resources
        if player.resources[resource_type_to_give] < total_cost:
            raise ValueError(f"Player needs {total_cost} {resource_type_to_give} but only has {player.resources[resource_type_to_give]}")
        
        # Execute trade
        player.resources[resource_type_to_give] -= total_cost
        player.resources[resource_type_to_receive] += amount_to_receive



    def _use_play_year_of_plenty(self, player: Player, resources_to_receive: list[str]):
        """
        Use a Year of Plenty development card to receive any two resources from the bank.
        
        The Year of Plenty card allows a player to take any two resources of their choice.
        The two resources can be the same type or different types.
        
        Args:
            player (Player): The player using the Year of Plenty card
            resources_to_receive (list[str]): List of two resources the player wants to receive
            
        Raises:
            AssertionError: If player doesn't have a Year of Plenty card
            AssertionError: If not exactly two resources are specified
            AssertionError: If any specified resource type is invalid
        """
        # Verify player has the card to use
        assert player.development_cards[DevelopmentCard.YEAR_OF_PLENTY] > 0, "Player does not have any year of plenty cards"
        
        # Verify exactly two resources were chosen
        assert len(resources_to_receive) == 2, "Player must choose 2 resources to receive"
        
        # Verify all chosen resources are valid resource types
        assert all(resource in RESOURCE_TYPES for resource in resources_to_receive), "Invalid resource type"
        
        # Remove the used card from player's hand
        player.development_cards[DevelopmentCard.YEAR_OF_PLENTY] -= 1
        
        # Give the chosen resources to the player
        for resource_type in resources_to_receive:
            player.resources[resource_type] += 1


    def _play_road_building(self, player: Player, edges_to_build: list[Edge]):
        """
        Use a Road Building development card to place up to two roads on the board.
        
        The Road Building card allows a player to build two roads at no resource cost.
        The roads must follow normal placement rules but don't require any resources.
        
        Args:
            player (Player): The player using the Road Building card
            edges_to_build (list[Edge]): List of edges where roads will be built (max 2)
            
        Raises:
            AssertionError: If player doesn't have a Road Building card
            AssertionError: If no edges are specified for building
        """
        # Verify player has the card to use
        assert player.development_cards[DevelopmentCard.ROAD_BUILDING] > 0, "Player does not have any road building cards"
        assert len(edges_to_build) > 0, "Player must build at least 1 road"


        # Place each road (with initial_placement=True to skip resource costs)
        for edge in edges_to_build:
            self._place_road(player, edge, True)

        # Remove the used card from player's hand
        player.development_cards[DevelopmentCard.ROAD_BUILDING] -= 1

    def _play_monopoly(self, player: Player, resource_type: str):
        """
        Use a Monopoly development card to take all of one resource type from other players.
        
        The Monopoly card allows a player to name one resource type and collect all cards
        of that type from all other players.
        
        Args:
            player (Player): The player using the Monopoly card
            resource_type (str): The type of resource to monopolize
            
        Raises:
            AssertionError: If player doesn't have a Monopoly card
            AssertionError: If the specified resource type is invalid
        """
        # Verify player has the card and resource type is valid
        assert player.development_cards[DevelopmentCard.MONOPOLY] > 0, "Player does not have any monopoly cards"
        assert resource_type in RESOURCE_TYPES, "Invalid resource type"

        # Collect the specified resource from all other players
        for p in self.players:
            if p != player:
                # Add other player's resources to the monopoly player
                player.resources[resource_type] += p.resources[resource_type]
                # Remove resources from other player
                p.resources[resource_type] = 0

        # Remove the used card from player's hand
        player.development_cards[DevelopmentCard.MONOPOLY] -= 1

    def _play_knight(self, coord_to_move_robber: tuple[int, int], player: Player, player_to_steal_from: Player):
        """
        Use a Knight development card to move the robber and steal a resource.
        
        The Knight card allows a player to:
        1. Move the robber to a new hex tile
        2. Steal one random resource from a player with a settlement/city adjacent to the new robber location
        
        Args:
            coord_to_move_robber (tuple[int, int]): New coordinates for the robber
            player (Player): The player using the Knight card
            player_to_steal_from (Player): The player to steal a resource from
            
        Raises:
            AssertionError: If player doesn't have a Knight card
            AssertionError: If trying to steal from self
            AssertionError: If robber is moved to current location
            AssertionError: If target player has no resources
            AssertionError: If target player has no settlement on the chosen tile
        """
        # Verify player has the card and basic rules
        assert player.development_cards[DevelopmentCard.KNIGHT] > 0, "Player does not have any knight cards"
        assert player_to_steal_from != player, "Cannot steal from yourself"
        assert coord_to_move_robber != self.board.robber, "Robber is already on the tile"

        # Move the robber to the new location
        self._move_robber(coord_to_move_robber)
        
        # Handle stealing if a target player is specified
        if player_to_steal_from is not None:
            # Verify target player has resources and a settlement on the robber tile
            assert sum(player_to_steal_from.resources.values()) > 0, "Player to steal from does not have any resources"
            assert any(vertex in self.board.tiles[coord_to_move_robber].vertices 
                      for vertex in player_to_steal_from.settlements), "Player to steal from does not have a settlement on the tile"
            # Steal a random resource
            self._steal_resource(player, player_to_steal_from)
      
        # Remove the used card from player's hand
        player.development_cards[DevelopmentCard.KNIGHT] -= 1
      

      
      





      
      
      
      

      