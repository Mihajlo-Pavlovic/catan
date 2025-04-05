# game/player.py

class Player:
    """
    Represents a player in the Catan game.
    
    Each player has a name, color, resource inventory, and keeps track of their
    settlements, roads, cities and victory points.
    
    Attributes:
        name (str): The player's name
        color (str): The player's color for game pieces
        resources (dict[str, int]): Dictionary tracking the count of each resource type
        settlements (list[Vertex]): List of vertex references where the player has settlements
        cities (list[Vertex]): List of vertex references where the player has cities
        roads (list[Edge]): List of edge references where the player has roads
        victory_points (int): Current number of victory points
    """
    def __init__(self, name: str, color: str):
        """
        Initialize a new player.

        Args:
            name (str): The player's name
            color (str): The player's color for game pieces
        """
        self.name = name
        self.color = color

        # Resource inventory
        self.resources = {
            "wood": 0,
            "brick": 0,
            "sheep": 0,
            "wheat": 0,
            "ore": 0
        }

        self.settlements = []  # list of vertex references
        self.cities = []        # list of vertex references
        self.roads = []        # list of edge references
        self.victory_points = 0

    def __repr__(self):
        """
        Returns a string representation of the player.

        Returns:
            str: A string showing the player's name and color
        """
        return f"Player {self.name} ({self.color})"

    def place_settlement(self, vertex):
        """
        Place a settlement at the specified vertex.
        
        Args:
            vertex (Vertex): The vertex where the settlement is being placed
        """
        self.settlements.append(vertex)

    def place_town(self, vertex_id):
        """
        Place a town at the specified vertex.
        
        Args:
            vertex_id (tuple): The ID of the vertex where the town is being placed
        """
        self.towns.append(vertex_id)
        
    def place_road(self, edge):
        """
        Place a road at the specified edge.
        
        Args:
            edge (Edge): The edge where the road is being placed
        """
        self.roads.append(edge)

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