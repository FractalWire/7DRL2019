from __future__ import annotations
import logging
from itertools import chain
from typing import Tuple, Dict
from math import log
import numpy as np
import tcod

from tcodplus.canvas import RootCanvas
from tcodplus.widgets import BaseMouseFocusable, BaseKeyboardFocusable
from tcodplus.style import Display, Origin, Border

import liberalguardians.common.data as data
import liberalguardians.common.topics as topics
from liberalguardians.common.logging import StyleAdapter
from liberalguardians.common.grid import AreaMask, Connections
from liberalguardians.common.grid import connection_to_coords
from liberalguardians.country import Country
from liberalguardians.ui.area import AreaUI
from liberalguardians.location import Location, get_adjacent_areas

logger = StyleAdapter(logging.getLogger(__name__))


BASE_AREA_SIZE = 11
AREA_MIN_SIZE = 3
AREA_MAX_SIZE = 23
BASE_DOOR_SIZE = 3

suspicion_str = dict(
    low=[[0, 20], "no alarm"],
    noisy=[[20, 40], "conservatives suspicious"],
    noticed=[[40, 60], "conservatives incoming"],
    high=[[60, 80], "conservatives in pursuit"],
    very_high=[[80, 100], "conservatives on your tail"]
)


def get_suspicion(suspicion: int) -> Tuple(str, str):
    for k, v in suspicion_str.items():
        low, high = v[0]
        if low <= suspicion <= high:
            return (k, v[1])


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


class LocationUI(BaseMouseFocusable, BaseKeyboardFocusable):
    def __init__(self, location: Location, *args, **kwargs) -> None:
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)
        self.location = location

        # self.template = template
        self.area_size = BASE_AREA_SIZE

        min_zoom = (round(log(AREA_MIN_SIZE/BASE_AREA_SIZE)/log(2)),)*2
        max_zoom = (round(log(AREA_MAX_SIZE/BASE_AREA_SIZE)/log(2)),)*2
        self.camera = Camera(min_zoom=min_zoom, max_zoom=max_zoom)

        for k, area in location.areas.items():
            style = dict(display=Display.NONE, border=Border.PATTERN2,
                         origin=Origin.CENTER, fg_color=tcod.black)
            area_ui = AreaUI(area, name=k, style=style)
            self.childs.add(area_ui)

        def movement_mask_update(start: Tuple[int, int], dest: Tuple[int, int]) -> None:
            x, y = start
            self.location.masks[y, x] |= AreaMask.FOG
            conn_rooms = get_adjacent_areas(
                (x, y), self.location.connections_grid[y, x])
            for x, y in conn_rooms:
                self.location.masks[y, x] |= AreaMask.FOG

            x, y = dest
            self.location.masks[y, x] |= (AreaMask.VISITED | AreaMask.VISIBLE)
            self.location.masks[y, x] &= ~AreaMask.FOG
            conn_rooms = get_adjacent_areas(
                (x, y), self.location.connections_grid[y, x])
            for x, y in conn_rooms:
                self.location.masks[y, x] |= AreaMask.VISIBLE
                self.location.masks[y, x] &= ~AreaMask.FOG

        def ev_keydown(ev: tcod.event.KeyDown) -> None:
            x, y = self.location.player_position
            connections = self.location.connections_grid[y, x]

            t_ev = tcod.event

            # TODO: key mapping outside
            motion_keys = [[t_ev.K_RIGHT, t_ev.K_d],
                           [t_ev.K_DOWN, t_ev.K_s],
                           [t_ev.K_LEFT, t_ev.K_q],
                           [t_ev.K_UP, t_ev.K_z]]
            if ev.sym in list(chain.from_iterable(motion_keys)):
                for i, m_keys in enumerate(motion_keys):
                    conn = 2**i
                    if ev.sym in m_keys and connections & conn:
                        dest = tuple(a+b for a, b
                                     in zip((x, y), connection_to_coords[conn]))
                        movement_mask_update((x, y), dest)
                        self.update_areas()

                        self.location.player_position = dest
                        area_ui = self.childs[str(dest)]
                        area_name = area_ui.area.area_name

                        value = area_ui.description
                        topics.description.publish(args=value)
                        topics.default_description.publish(args=value)

                        short = "{:<6}: {}".format(Connections(conn).name.capitalize(),
                                                   data.areas[area_name]['short_desc'])
                        topics.log.publish(args=dict(short=short))
                        break
                else:
                    topics.log.publish(args=dict(short="You can't go there"))

        def ev_mousewheel(ev: tcod.event.MouseWheel) -> None:
            mv = -(-1+ev.flipped*2) * ev.y
            if self.area_size <= AREA_MIN_SIZE and mv < 0:
                pass
            elif AREA_MAX_SIZE <= self.area_size and mv > 0:
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

        self.kbdfocus_requested = True

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))

    @property
    def description(self) -> Dict[str, str]:
        location = self.location
        template = location.template
        suspicion = location.suspicion
        masks = location.masks
        grid = location.connections_grid

        title = data.locations[template]['short_desc']
        subtitle = get_suspicion(suspicion)[1]
        text = data.locations[template]['long_desc'] + "\n\n"
        text += "You've visited {}% of it so far.".format(
            len(masks[masks & AreaMask.VISITED != 0]) * 100 // np.count_nonzero(grid))

        return dict(title=title, subtitle=subtitle, text=text)

    def update_areas(self):
        connections_grid = self.location.connections_grid
        g_h, g_w = connections_grid.shape
        for y in range(g_h):
            for x in range(g_w):
                if connections_grid[y, x]:
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

    import logging.config
    import yaml
    with open("logconfig.yml") as f:
        configdict = yaml.load(f, Loader=yaml.FullLoader)
    logging.config.dictConfig(configdict)
    logging.debug("test")

    root_w = root_h = 50
    root_canvas = RootCanvas(root_w, root_h, "room maze",
                             "data/fonts/dejavu10x10_gs_tc.png",
                             renderer=tcod.constants.RENDERER_OPENGL)
    location = Location(Country("LaLaLand"), "standard", (10, 10))
    location_ui = LocationUI(location, style=dict(width=1., height=1.))

    root_canvas.childs.add(location_ui)

    root_canvas.update_kbd_focus()

    tcod.sys_set_fps(60)
    while not tcod.console_is_window_closed():
        root_canvas.refresh()
        tcod.console_flush()
        handle_events(root_canvas)


if __name__ == '__main__':
    main()
