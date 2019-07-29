from enum import IntFlag, auto


class Connections(IntFlag):
    EAST = 2**0
    SOUTH = 2**1
    WEST = 2**2
    NORTH = 2**3
    ALL = NORTH | SOUTH | EAST | WEST


# format (x,y)
coords_to_connection = {
    (0, 0): 0,
    (1, 0): Connections.EAST,
    (0, 1): Connections.SOUTH,
    (-1, 0): Connections.WEST,
    (0, -1): Connections.NORTH
}
connection_to_coords = {
    0: (0, 0),
    Connections.EAST: (1, 0),
    Connections.SOUTH: (0, 1),
    Connections.WEST: (-1, 0),
    Connections.NORTH: (0, -1),
}


class AreaMask(IntFlag):
    FOG = auto()
    VISIBLE = auto()
    VISITED = auto()
    HOSTILE = auto()
    ENTRANCE = auto()
    EXIT = auto()
    FORBIDDEN = auto()
