# game/player.py

from game.development_cards import DevelopmentCard
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
        self.development_cards = {
            DevelopmentCard.KNIGHT: 0,
            DevelopmentCard.VICTORY_POINT: 0,
            DevelopmentCard.ROAD_BUILDING: 0,
            DevelopmentCard.YEAR_OF_PLENTY: 0,
            DevelopmentCard.MONOPOLY: 0
        }

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


    def slash(self, resource_to_slash: dict[str, int]):
        """
        Remove (discard) specified resources from the player's inventory when a 7 is rolled.
        
        According to Catan rules:
        - Players with more than 7 cards must discard half (rounded down) when a 7 is rolled
        - Players can choose which cards to discard
        - The total number of discarded cards must exactly equal half their cards (rounded down)
        
        Args:
            resource_to_slash (dict[str, int]): Dictionary mapping resource types to amounts to discard
                Example: {"wood": 2, "brick": 1} will discard 2 wood and 1 brick
        
        Raises:
            AssertionError: If any of these conditions are violated:
                - Player has 7 or fewer resources (shouldn't be slashing)
                - Invalid resource type specified
                - Trying to slash more of a resource than player has
                - Trying to slash a negative amount
                - Total amount to slash doesn't equal half of player's resources
        
        Example:
            If player has 9 resources:
                player.slash({"wood": 2, "wheat": 2})  # Discards 4 resources (9//2 = 4)
            If player has 8 resources:
                player.slash({"wood": 2, "brick": 2})  # Discards 4 resources (8//2 = 4)
        """
        # Calculate required discard amount (half of total resources, rounded down)
        total_resources = sum(self.resources.values())
        required_discard = total_resources // 2
        
        # Verify player should be discarding (more than 7 cards)
        assert total_resources > 7, "Cannot slash if player has 7 or fewer resources"
        
        # Verify correct total amount being discarded
        actual_discard = sum(resource_to_slash.values())
        assert actual_discard == required_discard, \
            f"Must discard exactly {required_discard} cards, trying to discard {actual_discard} cards"
        
        # Validate each resource type and amount
        for resource_type, amount in resource_to_slash.items():
            # Verify resource type exists
            assert resource_type in self.resources, \
                f"Invalid resource type: {resource_type}"
            
            # Verify player has enough of this resource
            assert self.resources[resource_type] >= amount, \
                f"Not enough {resource_type}: have {self.resources[resource_type]}, trying to slash {amount}"
            
            # Verify non-negative amount
            assert amount >= 0, \
                f"Cannot slash negative amount: {amount}"
        
        # After all validation passes, perform the resource removal
        for resource_type, amount in resource_to_slash.items():
            self.resources[resource_type] -= amount

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
        print(f"  🏙️  Cities: {self.cities}")
        print(f"  🛤️  Roads: {self.roads}")
        print(f"  🎒 Resources: {self.resources}")