# game/player.py

class Player:
    """
    Represents a player in the Catan game.
    
    Each player has a name, color, resource inventory, and keeps track of their
    settlements, roads, and victory points.
    
    Attributes:
        name (str): The player's name
        color (str): The player's color for game pieces
        board (Board): Reference to the game board
        resources (dict): Dictionary tracking the count of each resource type
        settlements (list): List of vertex IDs where the player has settlements
        towns (list): List of vertex IDs where the player has towns
        roads (list): List of edge keys where the player has roads
        victory_points (int): Current number of victory points
    """
    def __init__(self, name: str, color: str, board):
        """
        Initialize a new player.

        Args:
            name (str): The player's name
            color (str): The player's color for game pieces
            board (Board): Reference to the game board
        """
        self.name = name
        self.color = color
        self.board = board

        # Resource inventory
        self.resources = {
            "wood": 0,
            "brick": 0,
            "sheep": 0,
            "wheat": 0,
            "ore": 0
        }

        self.settlements = []  # list of vertex IDs
        self.towns = []        # list of vertex IDs
        self.roads = []        # list of edge keys (tuple of 2 vertex IDs)
        self.victory_points = 0

    def __repr__(self):
        """
        Returns a string representation of the player.

        Returns:
            str: A string showing the player's name and color
        """
        return f"Player {self.name} ({self.color})"

    def place_settlement(self, vertex_id):
        """
        Place a settlement at the specified vertex.
        
        Args:
            vertex_id (tuple): The ID of the vertex where the settlement is being placed
            
        Raises:
            KeyError: If the vertex_id doesn't exist in the board
            AssertionError: If the vertex_id is not in the board's vertices
        """
        assert vertex_id in self.board.vertices, f"Vertex {vertex_id} does not exist on the board"
        self.settlements.append(vertex_id)

    def place_town(self, vertex_id):
        """
        Place a town at the specified vertex.
        
        Args:
            vertex_id (tuple): The ID of the vertex where the town is being placed
            
        Raises:
            KeyError: If the vertex_id doesn't exist in the board
            AssertionError: If the vertex_id is not in the board's vertices
        """
        assert vertex_id in self.board.vertices, f"Vertex {vertex_id} does not exist on the board"
        self.towns.append(vertex_id)
        
    def place_road(self, edge_key):
        """
        Place a road at the specified edge.
        
        Adds the edge to the player's list of roads.

        Args:
            edge_key (tuple): A tuple of two vertex IDs representing the edge
        """
        self.roads.append(edge_key)

    def gain_resource(self, resource_type: str, amount: int = 1):
        """
        Add resources to the player's inventory.

        Args:
            resource_type (str): The type of resource to add ('wood', 'brick', etc.)
            amount (int, optional): The amount of resource to add. Defaults to 1.
        """
        if resource_type in self.resources:
            self.resources[resource_type] += amount

    def print_status(self):
        """
        Display the player's current game status.
        
        Prints a formatted view of the player's:
        - Name and color
        - Victory points
        - Settlements
        - Roads
        - Resource inventory
        """
        print(f"  🧑‍🌾 {self.name} ({self.color})")
        print(f"  🏆 Victory Points: {self.victory_points}")
        print(f"  🏠 Settlements: {self.settlements}")
        print(f"  🛤️  Roads: {self.roads}")
        print(f"  🎒 Resources: {self.resources}")