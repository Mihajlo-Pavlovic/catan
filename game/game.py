#game/game.py
import random
from game.constants import ANY, MAX_SETTLEMENTS,MAX_CITIES,MAX_ROADS, PORT_RESOURCE_VERTEX_IDS_DICT, RESOURCE_TYPES
from game.board import Board, Edge, Vertex, Vertex_Id, Edge_Id
from game.player import Player

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

    #def setup(self):
        #for player in self.players:


    def _place_settlement(self, player: Player, vertex: Vertex):
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
            raise ValueError("Player does not have a settlement adjacent to this vertex")
        # Check if player has enough resources
        if len(player.settlements) >= MAX_SETTLEMENTS:
          raise ValueError("Player has too many settlements")
        if player.resources["wood"] < 1 or player.resources["brick"] < 1 or player.resources["sheep"] < 1 or player.resources["wheat"] < 1:
          raise ValueError("Player does not have enough resources to place a settlement")
        # Place settlement
        vertex.settlement = player
        player.settlements.append(vertex)
        # Remove resources from player
        player.resources["wood"] -= 1
        player.resources["brick"] -= 1
        player.resources["sheep"] -= 1
        player.resources["wheat"] -= 1
        player.victory_points += 1

    def _place_road(self, player: Player, edge : Edge):
        """
        Place a road for a player at the specified edge.
        
        This method enforces the following rules:
        - The edge must exist on the board
        - The edge must not be already occupied
        - The player must have required resources (1 wood, 1 brick)
        - The player must not exceed maximum roads
        
        Args:
            player (Player): The player placing the road
            edge_id (Edge_Id): The edge where the road will be placed
            
        Raises:
            AssertionError: If the edge doesn't exist on the board
            ValueError: If placement violates any game rules
        """
        assert edge.id in self.board.edges, f"Edge {edge} does not exist on the board"
        # Check if edge is already occupied
        if edge.road is not None:
          raise ValueError("Edge already has a road")
        # Check if player has enough resources
        if player.resources["wood"] < 1 or player.resources["brick"] < 1:
          raise ValueError("Player does not have enough resources to place a road")
        # Check if player has enough roads
        if len(player.roads) >= MAX_ROADS:
          raise ValueError("Player has too many roads")
        # Place road
        edge.road = player
        player.roads.append(edge)
        # Remove resources from player
        player.resources["wood"] -= 1
        player.resources["brick"] -= 1

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


        # Calculate total cost
        total_cost = amount_to_give * trade_rate

        # Verify player has enough resources
        if player.resources[resource_type_to_give] < total_cost:
            raise ValueError(f"Player needs {total_cost} {resource_type_to_give} but only has {player.resources[resource_type_to_give]}")
        
        # Execute trade
        player.resources[resource_type_to_give] -= total_cost
        player.resources[resource_type_to_receive] += amount_to_receive
      
      
      
      

      