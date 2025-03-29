VALID_COORDS = [
    (0, -2), (1, -2), (2, -2),
    (-1, -1), (0, -1), (1, -1), (2, -1),
    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
    (-2, 1), (-1, 1), (0, 1), (1, 1),
    (-2, 2), (-1, 2), (0, 2),
]

RESOURCE_TYPES = ["wood", "brick", "sheep", "wheat", "ore", "desert"]

RESOURCE_DISTRIBUTION = {
    "wood": 4,
    "brick": 3,
    "sheep": 4,
    "wheat": 4,
    "ore": 3,
    "desert": 1
}

NUMBER_TOKENS = [5,2,6,3,8,10,9,12,11,4,8,10,9,4,5,6,3,11]


CORDS_UNWRAPED = [(0, -2), (1, -2), (2, -2), (2, -1), (2, 0), (1,1), (0,2), (-1,2), (-2, 2), (-2, 1), (-2, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 1), (-1,1), (-1, 0), (0, 0)]

VERTEX_OFFSETS = [
    (0, -1, 3),   # corner 0 → belongs to tile (q, r-1), corner 3
    (1, -1, 4),   # corner 1 → (q+1, r-1), corner 4
    (1, 0, 5),    # corner 2 → (q+1, r), corner 5
    (0, 0, 0),    # corner 3 → owned by current tile
    (-1, 0, 1),   # corner 4 → (q-1, r), corner 1
    (-1, -1, 2),  # corner 5 → (q-1, r-1), corner 2
]

