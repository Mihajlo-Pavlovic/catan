# game/player.py

class Player:
    def __init__(self, name: str, color: str):
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

        self.settlements = []  # list of vertex IDs
        self.roads = []        # list of edge keys (tuple of 2 vertex IDs)
        self.victory_points = 0

    def __repr__(self):
        return f"Player {self.name} ({self.color})"

    def place_settlement(self, vertex_id):
        if vertex_id not in self.settlements:
            self.settlements.append(vertex_id)
            self.victory_points += 1

    def build_road(self, edge_key):
        if edge_key not in self.roads:
            self.roads.append(edge_key)

    def gain_resource(self, resource_type: str, amount: int = 1):
        if resource_type in self.resources:
            self.resources[resource_type] += amount

    def print_status(self):
        print(f"  🧑‍🌾 {self.name} ({self.color})")
        print(f"  🏆 Victory Points: {self.victory_points}")
        print(f"  🏠 Settlements: {self.settlements}")
        print(f"  🛤️  Roads: {self.roads}")
        print(f"  🎒 Resources: {self.resources}")