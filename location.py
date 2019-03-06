import random
from itertools import chain
from typing import Tuple, List
from math import cos, sin, pi, log
from enum import IntFlag, auto
import numpy as np
from tcodplus.canvas import RootCanvas
from tcodplus.widgets import BoxFocusable, BaseKeyboardFocusable
from tcodplus.style import Display, Origin, Border, draw_border
import tcod


class Connections(IntFlag):
    EAST = 2**0
    SOUTH = 2**1
    WEST = 2**2
    NORTH = 2**3
    ALL = NORTH | SOUTH | EAST | WEST


# format (x,y)
_coords_to_connection = {
    (0, 0): 0,
    (1, 0): Connections.EAST,
    (0, 1): Connections.SOUTH,
    (-1, 0): Connections.WEST,
    (0, -1): Connections.NORTH
}
_connection_to_coords = {
    0: (0, 0),
    Connections.EAST: (1, 0),
    Connections.SOUTH: (0, 1),
    Connections.WEST: (-1, 0),
    Connections.NORTH: (0, -1),
}


def open_doors(room_grid, start, end) -> List[List[int]]:
    grid_shape = room_grid.shape
    room_shape = [e-2 for e in grid_shape]
    visited = np.ones(grid_shape, bool)
    visited[1:-1, 1:-1] = np.zeros(room_shape, bool)
    room_cnt = 0
    max_room_cnt = int(0.5 * room_shape[0] * room_shape[1])

    def _open_doors(pos: Tuple[int, int], p_pos: Tuple[int, int],
                    is_firstpass: bool = False) -> None:
        nonlocal room_cnt
        x, y = pos
        p_con = _coords_to_connection[(p_pos[0] - x, p_pos[1] - y)]

        if visited[y, x]:
            room_grid[y, x] = room_grid[y, x] | p_con
            return
        visited[y, x] = True
        room_cnt += 1

        if is_firstpass and pos == end:
            room_grid[y, x] = p_con
            return

        if room_cnt >= max_room_cnt:
            room_grid[y, x] = p_con
            return

        available_cons = []
        for i in range(4):
            con_visited = visited[y+int(sin(i*pi/2)), x+int(cos(i*pi/2))]
            available_cons.append(int(not con_visited) * 2**i)

        available_cons = np.bitwise_or.reduce(available_cons)

        if not available_cons:
            room_grid[y, x] = p_con
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

        room_grid[y, x] = new_cons | p_con

        if is_firstpass:
            mand_cons_list = np.full(
                [4], 2)**np.arange(4) & new_cons & avail_mand_cons
            mand_cons_list = np.unique(mand_cons_list[mand_cons_list != 0])
            con = np.random.choice(mand_cons_list)
            new_pos = tuple(a+b for a, b
                            in zip(pos, _connection_to_coords[con]))
            _open_doors(new_pos, pos, True)
            new_cons = new_cons & ~con

        shuffled_cons = np.unique(np.full([4], 2)**np.arange(4) & new_cons)
        np.random.shuffle(shuffled_cons[shuffled_cons != 0])
        for con in shuffled_cons:
            new_pos = tuple(a+b for a, b
                            in zip(pos, _connection_to_coords[con]))
            _open_doors(new_pos, pos, False)
    _open_doors(start, start, True)

    return room_grid


def get_adjacent_areas(position: Tuple[int, int],
                       room_connection_mask: int) -> List[Tuple[int, int]]:
    x, y = position
    rooms_pos = []
    for i in range(4):
        if 2**i & room_connection_mask:
            con = (x+int(cos(i*pi/2)), y+int(sin(i*pi/2)))
            rooms_pos.append(con)
    return rooms_pos


class AreaMask(IntFlag):
    FOG = auto()
    VISIBLE = auto()
    VISITED = auto()
    HOSTILE = auto()
    ENTRANCE = auto()
    EXIT = auto()


class Camera:
    def __init__(self, position: Tuple[int, int] = (0, 0),
                 zoom: Tuple[int, int] = (0, 0),
                 min_position: Tuple[int, int] = (None,)*2,
                 max_position: Tuple[int, int] = (None,)*2,
                 min_zoom: Tuple[int, int] = (None,)*2,
                 max_zoom: Tuple[int, int] = (None,)*2):
        self.position = position
        self.zoom = zoom
        self.min_position = min_position
        self.max_position = max_position
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom


class Area(BoxFocusable):
    def __init__(self, coordinates: Tuple[int, int], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value = ""
        self.coordinates = coordinates

    def update(self) -> None:
        location = self.parent
        x, y = self.coordinates
        # connections = location.connections_grid[y, x]
        mask = location.masks[y, x]
        cx, cy = location.camera.position
        center = location.player_position
        dx, dy = x - center[0], y - center[1]
        area_size = location.area_size

        loc_width, loc_height = location.geometry[6:]
        origin_x, origin_y = loc_width // 2 + cx, loc_height // 2 + cy

        style = self.style

        style.width = area_size
        style.height = area_size
        style.x = origin_x + dx*area_size
        style.y = origin_y + dy*area_size

        if mask & AreaMask.VISIBLE:
            style.display = Display.INITIAL
            if mask & AreaMask.FOG:
                if not mask & AreaMask.VISITED:
                    style.bg_color = (100, 100, 0)
                else:
                    style.bg_color = (180,)*3
            elif mask & AreaMask.VISITED:
                style.bg_color = (220,)*3
            elif not mask & AreaMask.VISITED:
                style.bg_color = (200, 200, 0)
            elif mask & AreaMask.HOSTILE:
                style.bg_color = (200, 0, 0)

            if mask & AreaMask.ENTRANCE:
                style.fg_color = (0, 200, 0)
            elif mask & AreaMask.EXIT:
                style.fg_color = (200, 0, 0)
        else:
            style.display = Display.NONE

        self.update_geometry(True)
        self.console.clear(bg=self.style.bg_color, fg=self.style.fg_color)
        self.draw_area()

        # draw connections
        # w, h = self.geometry[6:]
        # for i in range(4):
        #     if 2**i & connections:
        #         x = round((int(cos(i*pi/2))+1)*((w-1)/2))
        #         y = round((int(sin(i*pi/2))+1) * ((h-1)/2))
        #         self.console.bg[y, x] = (0, 0, 255)

        self.should_update = False

    def draw_area(self):
        x, y = self.coordinates
        mask = self.parent.masks[y, x]
        # area_content = self.geometry.content_width

        if mask & AreaMask.VISIBLE:
            if mask & AreaMask.FOG:
                if not mask & AreaMask.VISITED:
                    self.console.ch[:] = ord('?')
                    self.console.fg[:] = (50,)*3

                    # self.console.print_box(0, area_content // 2, area_content,
                    #                        area_content, "NO INTEL",
                    #                        alignment=tcod.constants.CENTER)
                else:
                    pass
            elif mask & AreaMask.VISITED:
                pass
            elif not mask & AreaMask.VISITED:
                self.console.ch[:] = ord('?')
                self.console.fg[:] = (100,)*3
                # self.console.print_box(0, area_content // 2, area_content, area_content,
                #                        "???", alignment=tcod.constants.CENTER)
            elif mask & AreaMask.HOSTILE:
                pass

    def draw(self) -> None:
        """draw the Canvas to the parent Canvas"""

        style = self.styles()

        con = None
        if style.border != Border.NONE:
            con = tcod.console.Console(*self.geometry[4:6])
            draw_border(con, style)
            self.console.blit(con, 1, 1)

        else:
            con = self.console

        # draw coordinates
        x, y = self.coordinates
        connections = self.parent.connections_grid[y, x]

        x, y, width, height = self.geometry[2:6]
        for i in range(4):
            if 2**i & connections:
                cosipi_2 = int(cos(i*pi/2))
                sinipi_2 = int(sin(i*pi/2))

                # door position
                conn_x = round((cosipi_2+1) * ((width-1)/2))
                conn_y = round((sinipi_2+1) * ((height-1)/2))

                # door size
                door_size = self.parent.area_size // 3
                door_size = door_size + int(not door_size % 2)
                if cosipi_2 == 0:
                    c_x_start = conn_x - door_size//2
                    c_x_stop = c_x_start + door_size
                    c_y_start = conn_y
                    c_y_stop = conn_y + 1
                else:
                    c_y_start = conn_y - door_size//2
                    c_y_stop = c_y_start + door_size
                    c_x_start = conn_x
                    c_x_stop = conn_x + 1

                con.ch[c_y_start:c_y_stop, c_x_start:c_x_stop] = ord(' ')
                con.bg[c_y_start:c_y_stop, c_x_start:c_x_stop] = style.bg_color

        con.blit(self.parent.console, x, y, 0, 0, width, height,
                 style.fg_alpha, style.bg_alpha, style.key_color)

    # def base_drawing(self) -> None:
    #     super().base_drawing()


_BASE_AREA_SIZE = 11
_AREA_MIN_SIZE = 3
_AREA_MAX_SIZE = 23
_BASE_DOOR_SIZE = 3


class Location(BoxFocusable, BaseKeyboardFocusable):
    def __init__(self, grid_width: int, grid_height: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # self.grid_width = grid_width
        # self.grid_height = grid_height
        self.area_size = _BASE_AREA_SIZE
        min_zoom = (round(log(_AREA_MIN_SIZE/_BASE_AREA_SIZE)/log(2)),)*2
        max_zoom = (round(log(_AREA_MAX_SIZE/_BASE_AREA_SIZE)/log(2)),)*2

        self.camera = Camera(min_zoom=min_zoom, max_zoom=max_zoom)

        conn_grid = np.zeros((grid_height, grid_width), np.int8)
        self.entrance = (1, random.randrange(1, grid_height-1))
        self.exit = (grid_width-2, random.randrange(1, grid_height-1))
        self.player_position = self.entrance
        conn_grid = open_doors(conn_grid, self.entrance, self.exit)

        self.connections_grid = conn_grid
        self.masks = np.zeros(conn_grid.shape, np.int8)
        ex, ey = self.entrance
        self.masks[ey, ex] |= AreaMask.ENTRANCE
        ex, ey = self.exit
        self.masks[ey, ex] |= AreaMask.EXIT

        room_w = room_h = 3

        for j in range(grid_height):
            for i in range(grid_width):
                style = dict(x=(1+i)+i*room_w, y=(1+j)+j*room_h, width=room_w,
                             height=room_h, display=Display.NONE,
                             border=Border.PATTERN2, origin=Origin.CENTER,
                             fg_color=tcod.black)
                area = Area((i, j), name=str((i, j)), style=style)
                self.childs.add(area)

        self.kbdfocus_requested = True

        def movement_mask_update(start: Tuple[int, int], dest: Tuple[int, int]) -> None:
            x, y = start
            self.masks[y, x] |= AreaMask.FOG
            conn_rooms = get_adjacent_areas(
                (x, y), self.connections_grid[y, x])
            for x, y in conn_rooms:
                self.masks[y, x] |= AreaMask.FOG

            x, y = dest
            self.masks[y, x] |= (AreaMask.VISITED | AreaMask.VISIBLE)
            self.masks[y, x] &= ~AreaMask.FOG
            conn_rooms = get_adjacent_areas(
                (x, y), self.connections_grid[y, x])
            for x, y in conn_rooms:
                self.masks[y, x] |= AreaMask.VISIBLE
                self.masks[y, x] &= ~AreaMask.FOG

        def ev_keydown(ev: tcod.event.KeyDown) -> None:
            x, y = self.player_position
            connections = self.connections_grid[y, x]

            t_ev = tcod.event
            motion_keys = [[t_ev.K_d, t_ev.K_RIGHT],
                           [t_ev.K_DOWN, t_ev.K_s],
                           [t_ev.K_LEFT, t_ev.K_q],
                           [t_ev.K_UP, t_ev.K_z]]
            if ev.sym in list(chain.from_iterable(motion_keys)):
                for i, m_keys in enumerate(motion_keys):
                    conn = 2**i
                    if ev.sym in m_keys and conn & connections:
                        dest = tuple(a+b for a, b
                                     in zip((x, y), _connection_to_coords[conn]))
                        movement_mask_update((x, y), dest)
                        self.update_areas()

                        self.player_position = dest
                        break
                else:
                    print("Can't go there!")

        def ev_mousewheel(ev: tcod.event.MouseWheel) -> None:
            mv = -(-1+ev.flipped*2) * ev.y
            if self.area_size <= _AREA_MIN_SIZE and mv < 0:
                pass
            elif _AREA_MAX_SIZE <= self.area_size and mv > 0:
                pass
            else:
                self.area_size += 2*mv

            self.update_areas()

        def ev_mousemotion(ev: tcod.event.MouseMotion):
            # Drag
            dcx = dcy = 0
            x, y = self.camera.position
            if ev.state & tcod.event.BUTTON_LMASK:
                dcx, dcy = ev.tile_motion
                if dcx:
                    x += dcx
                if dcy:
                    y += dcy
                if dcx or dcy:
                    self.camera.position = (x, y)
                    self.update_areas()

        def ev_mousebuttonup(ev: tcod.event.MouseButtonUp):
            self.camera.position = (0, 0)
            self.update_areas()

        self.focus_dispatcher.ev_keydown.append(ev_keydown)
        self.focus_dispatcher.ev_mousewheel.append(ev_mousewheel)
        self.focus_dispatcher.ev_mousemotion.append(ev_mousemotion)
        self.focus_dispatcher.ev_mousebuttonup.append(ev_mousebuttonup)

        x, y = self.player_position
        self.masks[y, x] |= (AreaMask.VISITED | AreaMask.VISIBLE)
        self.masks[y, x] &= ~AreaMask.FOG
        conn_rooms = get_adjacent_areas((x, y), self.connections_grid[y, x])
        for x, y in conn_rooms:
            self.masks[y, x] |= AreaMask.VISIBLE
            self.masks[y, x] &= ~AreaMask.FOG
        # self.should_update = True

    def update_areas(self):
        g_h, g_w = self.connections_grid.shape
        for y in range(g_h):
            for x in range(g_w):
                self.childs[str((x, y))].should_update = True

    def update(self):
        # x, y = self.player_position
        # self.masks[y, x] |= (AreaMask.VISITED | AreaMask.VISIBLE)
        # self.masks[y, x] &= ~AreaMask.FOG
        # conn_rooms = get_adjacent_areas((x, y), self.connections_grid[y, x])
        # for x, y in conn_rooms:
        #     self.masks[y, x] |= AreaMask.VISIBLE
        #     self.masks[y, x] &= ~AreaMask.FOG
        self.should_update = False


def main() -> None:
    def handle_events(root_canvas: RootCanvas) -> None:
        for event in tcod.event.get():
            if event.type == "KEYDOWN" and event.sym == tcod.event.K_ESCAPE:
                raise SystemExit()
            root_canvas.handle_focus_event(event)

    root_w = root_h = 50
    root_canvas = RootCanvas(root_w, root_h, "room maze",
                             "data/fonts/dejavu10x10_gs_tc.png",
                             renderer=tcod.constants.RENDERER_OPENGL)
    location = Location(10, 10, style=dict(width=1., height=1.))

    root_canvas.childs.add(location)

    root_canvas.update_kbd_focus()

    tcod.sys_set_fps(60)
    while not tcod.console_is_window_closed():
        root_canvas.refresh()
        tcod.console_flush()
        handle_events(root_canvas)


if __name__ == '__main__':
    main()
