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

VERTEX_OFFSETS  = [
    (-1, -2),  # top-left
    (1, -2),   # top-right
    (2, 0),    # right
    (1, 2),    # bottom-right
    (-1, 2),   # bottom-left
    (-2, 0),   # left
]

MAX_SETTLEMENTS = 5
MAX_ROADS = 15
MAX_CITIES = 4

