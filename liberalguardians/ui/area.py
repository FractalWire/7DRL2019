from __future__ import annotations
from math import cos, sin, pi
import tcod

from tcodplus.widgets import BaseMouseFocusable
from tcodplus.style import Display, Border, draw_border
import liberalguardians.common.data as data
import liberalguardians.common.topics as topics
from liberalguardians.common.grid import AreaMask
from liberalguardians.area import Area


class AreaUI(BaseMouseFocusable):
    def __init__(self, area: Area, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.area = area
        # self.coordinates = coordinates

        def ev_mousefocusgain(ev: tcod.event.MouseMotion, self=self) -> None:
            value = self.description
            topics.description.publish(args=value)

        def ev_mousefocuslost(ev: tcod.event.MouseMotion, self=self) -> None:
            topics.description.publish(args={})

        self.focus_dispatcher.ev_mousefocusgain.append(ev_mousefocusgain)
        self.focus_dispatcher.ev_mousefocuslost.append(ev_mousefocuslost)

    @property
    def description(self):
        location = self.area.location
        x, y = self.area.coordinates
        mask = location.masks[y, x]

        area_name = self.area.area_name
        title = data.areas[area_name]['short_desc']

        text = "\t{:c}{:c}{:c}{:c}{}{:c}\n\n\n".format(
            tcod.COLCTRL_FORE_RGB, *
            (150,)*3, data.areas[area_name]['long_desc'],
            tcod.COLCTRL_STOP)

        center = location.player_position
        dx, dy = x - center[0], y - center[1]
        if mask & AreaMask.FORBIDDEN and not (dx == dy == 0):
            restricted_str = ("This is a restricted area, going there will "
                              "probably make the conservatives angry...")
            text += "\t{:c}{:c}{:c}{:c}{}{:c}\n\n\n".format(
                tcod.COLCTRL_FORE_RGB, *(200, 20, 20), restricted_str, tcod.COLCTRL_STOP)

        if not mask & AreaMask.VISITED:
            text += "You never been to this place."
        elif mask & AreaMask.FOG:
            text += "You can't see what's in there. This area is too far away..."
        else:
            text += "{} people are present here :\n\n".format(
                len(self.area.characters))

            iter_chars = iter(self.area.characters)
            text += "\n".join(f'{c1.colored_profession:<17}{c2.colored_profession}'
                              for c1, c2 in zip(iter_chars, iter_chars))
            if len(self.area.characters) % 2:
                text += f"\n{self.area.characters[-1].colored_profession}"

        interactions = ""
        if self.name == str(center):
            interactions = self.get_interactions()
        return dict(title=title, text=text, interactions=interactions)

    def get_interactions(self):
        area_name = self.area.area_name
        return data.areas[area_name]['interactions']

    def update(self) -> None:
        location = self.area.location
        locationUI = self.parent
        x, y = self.area.coordinates
        # connections = location.connections_grid[y, x]
        mask = location.masks[y, x]
        cx, cy = locationUI.camera.position
        center = location.player_position
        dx, dy = x - center[0], y - center[1]
        area_size = locationUI.area_size

        loc_width, loc_height = locationUI.geometry[6:]
        origin_x, origin_y = loc_width // 2 + cx, loc_height // 2 + cy

        self.style.width = area_size
        self.style.height = area_size
        self.style.x = origin_x + dx*area_size
        self.style.y = origin_y + dy*area_size

        # TODO: put the various styles into a single dict
        # TODO: color scheme with fixed name
        if mask & AreaMask.VISIBLE:
            self.style.display = Display.INITIAL

            if mask & AreaMask.FOG:
                if not mask & AreaMask.VISITED:
                    if mask & AreaMask.HOSTILE:
                        self.style.bg_color = (200, 0, 0)
                    elif mask & AreaMask.FORBIDDEN:
                        self.style.bg_color = (20,)*3
                    else:
                        self.style.bg_color = (100, 100, 0)
                else:
                    if mask & AreaMask.HOSTILE:
                        self.style.bg_color = (200, 0, 0)
                    elif mask & AreaMask.FORBIDDEN:
                        self.style.bg_color = (20,)*3
                    else:
                        self.style.bg_color = (180,)*3
            elif mask & AreaMask.VISITED:
                if mask & AreaMask.FORBIDDEN:
                    self.style.bg_color = (30,)*3
                else:
                    self.style.bg_color = (220,)*3
            elif not mask & AreaMask.VISITED:
                if mask & AreaMask.FORBIDDEN:
                    self.style.bg_color = (30,)*3
                else:
                    self.style.bg_color = (200, 200, 0)
            elif mask & AreaMask.HOSTILE:
                self.style.bg_color = (200, 0, 0)

            if mask & AreaMask.ENTRANCE:
                self.style.fg_color = (0, 200, 0)
            elif mask & AreaMask.EXIT:
                self.style.fg_color = (200, 0, 0)
            else:
                self.style.fg_color = tcod.black
        else:
            self.style.display = Display.NONE

        mixed_style = self.styles()  # TODO: Useless for now
        self.update_geometry(True)
        self.console.clear(bg=mixed_style.bg_color, fg=mixed_style.fg_color)
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
        location = self.area.location
        area_size = self.parent.area_size
        x, y = self.area.coordinates
        mask = location.masks[y, x]
        # area_content = self.geometry.content_width

        if mask & AreaMask.VISIBLE:
            if mask & AreaMask.FOG:
                if not mask & AreaMask.VISITED:
                    self.console.ch[:] = ord('?')
                    if mask & AreaMask.FORBIDDEN:
                        self.console.fg[:] = (100,)*3
                    else:
                        self.console.fg[:] = (50,)*3

                    # self.console.print_box(0, area_content // 2, area_content,
                    #                        area_content, "NO INTEL",
                    #                        alignment=tcod.constants.CENTER)
                else:
                    pass
            elif mask & AreaMask.VISITED:
                center = location.player_position
                dx, dy = x - center[0], y - center[1]
                if dx == dy == 0:
                    self.console.bg[:] = (220,)*3
                    party_x = party_y = area_size//2-1
                    self.console.print(party_x, party_y, '@', fg=tcod.black)
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

        # TODO: Border here, really ?
        if style.border != Border.NONE:
            console = tcod.console.Console(*self.geometry[4:6])
            draw_border(console, style)
            self.console.blit(console, 1, 1)

        else:
            console = self.console

        # draw coordinates
        location = self.area.location
        locationUI = self.parent
        x, y = self.area.coordinates
        connections = location.connections_grid[y, x]

        x, y, width, height = self.geometry[2:6]
        for i in range(4):
            if 2**i & connections:
                cosipi_2 = int(cos(i*pi/2))
                sinipi_2 = int(sin(i*pi/2))

                # door position
                conn_x = round((cosipi_2+1) * ((width-1)/2))
                conn_y = round((sinipi_2+1) * ((height-1)/2))

                # door size
                door_size = locationUI.area_size // 3
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

                console.ch[c_y_start:c_y_stop, c_x_start:c_x_stop] = ord(' ')
                console.bg[c_y_start:c_y_stop,
                           c_x_start:c_x_stop] = style.bg_color

        console.blit(locationUI.console, x, y, 0, 0, width, height,
                     style.fg_alpha, style.bg_alpha, style.key_color)
