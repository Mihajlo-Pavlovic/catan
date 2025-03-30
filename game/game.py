#game/game.py
import random
from game.constants import MAX_SETTLEMENTS,MAX_CITIES,MAX_ROADS
from game.board import Board, Vertex_Id, Edge_Id
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


    def _place_settlement(self, player: Player, vertex_id: Vertex_Id):
        """
        Place a settlement for a player at the specified vertex.
        
        This method enforces the following rules:
        - The vertex must exist on the board
        - The vertex must not be already occupied
        - The player must have adjacent settlements
        - The player must not exceed maximum settlements
        - The player must have required resources (1 wood, 1 brick, 1 sheep, 1 wheat)
        
        Args:
            player (Player): The player placing the settlement
            vertex_id (Vertex_Id): The vertex where the settlement will be placed
            
        Raises:
            AssertionError: If the vertex doesn't exist on the board
            ValueError: If placement violates any game rules
        """
        assert vertex_id in self.board.vertices, f"Vertex {vertex_id} does not exist on the board"
        vertex = self.board.vertices[vertex_id]
        # Check if vertex is already occupied
        if vertex.settlement is not None:
          raise ValueError("Vertex already has a settlement")
      # For each adjacent vertex check if the player has a settlement, if not, raise an error
        for adjacent_vertex in vertex.adjacent_vertices:
          if self.board.vertices[adjacent_vertex].settlement is None:
            raise ValueError("Player does not have a settlement adjacent to this vertex")
        # Check if player has enough resources
        if len(player.settlements) >= MAX_SETTLEMENTS:
          raise ValueError("Player has too many settlements")
        if player.resources["wood"] < 1 or player.resources["brick"] < 1 or player.resources["sheep"] < 1 or player.resources["wheat"] < 1:
          raise ValueError("Player does not have enough resources to place a settlement")
        # Place settlement
        vertex.settlement = player
        player.settlements.append(vertex_id)
        # Remove resources from player
        player.resources["wood"] -= 1
        player.resources["brick"] -= 1
        player.resources["sheep"] -= 1
        player.resources["wheat"] -= 1
        player.victory_points += 1

    def _place_road(self, player: Player, edge_id: Edge_Id):
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
        assert edge_id in self.board.edges, f"Edge {edge_id} does not exist on the board"
        edge = self.board.edges[edge_id]
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
        player.roads.append(edge_id)
        # Remove resources from player
        player.resources["wood"] -= 1
        player.resources["brick"] -= 1
    def _place_city(self, player: Player, vertex_id: Vertex_Id):
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
        assert vertex_id in self.board.vertices, f"Vertex {vertex_id} does not exist on the board"
        vertex = self.board.vertices[vertex_id]
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
        player.cities.append(vertex_id)
        player.settlements.remove(vertex_id)
        # Remove resources from player
        player.resources["wheat"] -= 2
        player.resources["ore"] -= 3
        player.victory_points += 1


    def _get_resource_from_vertex(self, vertex_id: Vertex_Id):
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
        vertex = self.board.vertices[vertex_id]
        return [self.board.tiles[coord].resource_type for coord in vertex.adjacent_tiles]
    
    
    def _distribute_initial_resources(self):
        """
        Distribute initial resources to each player.
        """
        for player in self.players:
          for vertex_id in player.settlements:
            for resource_type in self._get_resource_from_vertex(vertex_id):
              player.resources[resource_type] += 1

    def _distribute_resources(self, dice_roll: int):
      """
      Distribute resources to the players based on the dice roll.

      Args:
        dice_roll (int): The dice roll to distribute resources for
      """
      tilesThatCanGiveResource = self.board.number_tile_dict[dice_roll]
      tilesThatCanGiveResource= tilesThatCanGiveResource.filter(lambda tile: tile.cord != self.board.robber)
      for tile in tilesThatCanGiveResource:
        for player in self.players:
          if tile.cord in player.settlements:
            player.resources[tile.resource_type] += 1
          if tile.cord in player.cities:
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



      
      

      