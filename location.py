from __future__ import annotations
from typing import Tuple, List
import random as rnd
from math import cos, sin, pi
import numpy as np
import common.data as data
from common.grid import Connections, coords_to_connection, connection_to_coords, AreaMask
from country import Country
from area import Area


def get_adjacent_areas(position: Tuple[int, int],
                       room_connection_mask: int) -> List[Tuple[int, int]]:
    x, y = position
    rooms_pos = []
    for i in range(4):
        if 2**i & room_connection_mask:
            con = (x+int(cos(i*pi/2)), y+int(sin(i*pi/2)))
            rooms_pos.append(con)
    return rooms_pos


def open_doors(grid, start, end) -> List[List[int]]:
    grid_h, grid_w = grid.shape
    visited = np.zeros(grid.shape, bool)
    room_cnt = 0
    max_room_cnt = int(0.5 * grid_h * grid_w)

    def _open_doors(pos: Tuple[int, int], p_pos: Tuple[int, int],
                    is_firstpass: bool = False) -> None:
        nonlocal room_cnt
        x, y = pos
        p_con = coords_to_connection[(p_pos[0] - x, p_pos[1] - y)]

        if visited[y, x]:
            grid[y, x] = grid[y, x] | p_con
            return
        visited[y, x] = True
        room_cnt += 1

        if is_firstpass and pos == end:
            grid[y, x] = p_con
            return

        if room_cnt >= max_room_cnt:
            grid[y, x] = p_con
            return

        available_cons = 0
        for i in range(4):
            dx, dy = round(cos(i*pi/2)), round(sin(i*pi/2))
            if 0 <= y+dy < grid_h and 0 <= x+dx < grid_w:
                con_visited = visited[y+dy, x+dx]
                available_cons += int(not con_visited) * 2**i

        # available_cons = np.bitwise_or.reduce(available_cons)

        if not available_cons:
            grid[y, x] = p_con
            return

        choices = np.unique(np.arange(1, 16) & available_cons)
        choices = choices[choices != 0]

        new_cons = np.random.choice(choices)

        if is_firstpass:
            vertical_cons = Connections.NORTH | Connections.SOUTH
            if x == end[0]:
                vertical_cons = Connections.NORTH if y > end[1] \
                    else Connections.SOUTH
            mandatory_cons = Connections.EAST | vertical_cons
            avail_mand_cons = available_cons & mandatory_cons
            if not (new_cons & avail_mand_cons):
                choices = np.unique(np.arange(1, 16) & avail_mand_cons)
                choices = choices[choices != 0]
                new_cons = new_cons | np.random.choice(choices)

        grid[y, x] = new_cons | p_con

        if is_firstpass:
            mand_cons_list = np.full(
                [4], 2)**np.arange(4) & new_cons & avail_mand_cons
            mand_cons_list = np.unique(mand_cons_list[mand_cons_list != 0])
            con = np.random.choice(mand_cons_list)
            new_pos = tuple(a+b for a, b
                            in zip(pos, connection_to_coords[con]))
            _open_doors(new_pos, pos, True)
            new_cons = new_cons & ~con

        shuffled_cons = np.unique(np.full([4], 2)**np.arange(4) & new_cons)
        np.random.shuffle(shuffled_cons[shuffled_cons != 0])
        for con in shuffled_cons:
            new_pos = tuple(a+b for a, b
                            in zip(pos, connection_to_coords[con]))
            _open_doors(new_pos, pos, False)
    _open_doors(start, start, True)

    return grid


class Location:
    def __init__(self, country: Country, template: str, grid_shape: Tuple[int, int]):
        self.template = template
        self.suspicion = 0
        self.country = country

        # init grid
        grid_height, grid_width = grid_shape
        self.entrance = (0, rnd.randrange(0, grid_height))
        self.exit = (grid_width-1, rnd.randrange(0, grid_height))
        self.player_position = self.entrance
        conn_grid = np.zeros(grid_shape, np.int8)
        conn_grid = open_doors(conn_grid, self.entrance, self.exit)
        self.connections_grid = conn_grid

        # init areas masks
        self.masks = np.zeros(grid_shape, np.int8)
        ex, ey = self.entrance
        self.masks[ey, ex] |= AreaMask.ENTRANCE
        ex, ey = self.exit
        self.masks[ey, ex] |= AreaMask.EXIT

        x, y = self.player_position
        self.masks[y, x] |= (AreaMask.VISITED | AreaMask.VISIBLE)
        self.masks[y, x] &= ~AreaMask.FOG
        conn_positions = get_adjacent_areas((x, y), self.connections_grid[y, x])
        for x, y in conn_positions:
            self.masks[y, x] |= AreaMask.VISIBLE
            self.masks[y, x] &= ~AreaMask.FOG

        # Create Areas here
        self.areas = {}
        available_areas = data.locations[self.template]["areas"]
        for j in range(grid_height):
            for i in range(grid_width):
                if self.connections_grid[j, i]:
                    area_name = rnd.choices(*zip(*available_areas.items()))[0]
                    area = Area(self, (i, j), area_name)
                    area.randomize()
                    self.areas[str((i, j))] = area
                    if "forbidden" in data.areas[area_name] and data.areas[area_name]["forbidden"]:
                        self.masks[j, i] |= AreaMask.FORBIDDEN
