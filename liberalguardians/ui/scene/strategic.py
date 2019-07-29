from __future__ import annotations
from typing import List, Dict, Any
import logging
import tcod

from tcodplus.canvas import Canvas, RootCanvas
from tcodplus.widgets import BaseUpdatable, BaseMouseFocusable, Text, Header, Image
from tcodplus.style import Origin, Border, Display

import liberalguardians.common.data as data
import liberalguardians.common.topics as topics
from liberalguardians.common.logging import StyleAdapter
from liberalguardians.characters import Character
from liberalguardians.country import Country
from liberalguardians.location import Location
from liberalguardians.ui.log import LogUI
from liberalguardians.ui.location import LocationUI, get_suspicion

logger = StyleAdapter(logging.getLogger(__name__))


class InfosPanel(BaseMouseFocusable):
    def __init__(self, *args, **kwargs):
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)
        header_style = dict(width=1., height=1, bg_alpha=0)

        country_name = Header("", name='country_name', style=header_style)
        suspicion_desc = Header("", isupper=False, name='suspicion',
                                style={**header_style, "y": 1})

        self.childs.add(country_name, suspicion_desc)

        def ev_mousefocusgain(ev: tcod.event.MouseMotion, infos=self) -> None:
            topics.description.publish(args=self.description)

        def ev_mousefocuslost(ev: tcod.event.MouseMotion, infos=self) -> None:
            topics.description.publish()

        self.focus_dispatcher.ev_mousefocusgain.append(ev_mousefocusgain)
        self.focus_dispatcher.ev_mousefocuslost.append(ev_mousefocuslost)

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))

    @property
    def description(self) -> Dict[str, str]:
        # TODO: avoid DOM mishmash lookup here
        country = self.parent.country
        location = self.parent.childs['location']
        # characters = self.parent.childs['characters']

        # location description
        location_desc = location.description
        country_desc = country.description
        # party description

        title = "\t"+country_desc['title']
        subtitle = country_desc['subtitle']
        text = country_desc['text'] + "\n\n"
        text += "You're in a {}.\n\n".format(location_desc['title'])
        text += location_desc['text']
        return dict(title=title, subtitle=subtitle, text=text)

    def update(self) -> None:
        self.should_update = False

    def base_drawing(self):
        super().base_drawing()
        country = self.parent.country
        location_ui = self.parent.childs['location']
        location = location_ui.location
        self.childs['country_name'].value = "\t{} - {}".format(
            country.name, data.locations[location.template]['short_desc'])

        # self.childs['alignment_name'].value = country.alignment
        liberal_width = round(((country.mood+1000)/2000) *
                              self.geometry.content_width)
        self.console.bg[0, :] = (150, 0, 0)
        self.console.bg[0, :liberal_width] = (0, 150, 0)
        self.console.bg[1, :] = (0, 15, 15)
        # self.console.bg[1, :liberal_width] = (0, 150, 0)

        self.childs['suspicion'].value = "{}".format(
            get_suspicion(location.suspicion)[1].capitalize())


class CharacterPortrait(BaseMouseFocusable):
    def __init__(self, character: Character, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.character = character

        def ev_mousefocusgain(ev: tcod.event.MouseMotion,
                              portrait: Character = self) -> None:
            value = portrait.character.description
            topics.description.publish(args=value)

        def ev_mousefocuslost(ev: tcod.event.MouseMotion,
                              portrait: Character = self) -> None:
            topics.description.publish()

        self.focus_dispatcher.ev_mousefocusgain.append(ev_mousefocusgain)
        self.focus_dispatcher.ev_mousefocuslost.append(ev_mousefocuslost)

    def update(self) -> None:
        img_path = f"{data.img_dir}/{self.character.sex}/{self.character.img}"
        img = tcod.image_load(img_path)
        img.scale(2*self.geometry.content_width, 2*self.geometry.content_height)
        img.blit_2x(self.console, 0, 0)
        self.should_update = False


class CharactersPanel(BaseUpdatable):
    def __init__(self, *args, characters: List[Character] = list(),
                 **kwargs) -> None:
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)
        self.characters = characters
        self.should_update = True
        self.ischar_init = False  # TODO: Quick and dirty here...

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))

    def update(self) -> None:
        if not self.ischar_init:
            width, height = self.geometry[6:]
            max_char_cnt = len(self.characters)
            img_w = width
            img_h = height//max_char_cnt
            img_size = min(img_w, img_h)
            self.childs.clear()
            portrait_style = dict(x=1., width=img_size, origin=Origin.TOP_RIGHT,
                                  height=img_size)

            for i, c in enumerate(self.characters):
                y = i*img_size
                portrait_style = {**portrait_style, "y": y}
                char_portrait = CharacterPortrait(c, style=portrait_style)

                self.childs.add(char_portrait)
                char_portrait.should_update = True

            self.ischar_init = True

        self.should_update = False


class DescriptionPanel(Canvas):
    def __init__(self, value: Dict[str, str], *args, **kwargs) -> None:
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)
        title_style = dict(y=1, width=1., height=1)
        subtitle_style = dict(y=2, width=1., height=1)
        text_style = dict(y=4, width=1., height="-3+1.", border=Border.EMPTY)
        img_style = dict(y=4, border=Border.EMPTY, display=Display.NONE)
        interactions_style = dict(
            y=4, border=Border.EMPTY, display=Display.NONE)

        title = Header("", name="title", style=title_style)
        subtitle = Header("", isupper=False, name="subtitle",
                          style=subtitle_style)
        text = Text("", auto_height=True, name="text", style=text_style)
        image = Image("", name="img", style=img_style)
        interactions = InteractionsPanel(name="interactions",
                                         style=interactions_style)

        self.childs.add(title, subtitle, text, image, interactions)

        self._value = {}
        self.default_value = {}
        self.value = value

        topics.description.subscribe(self._ev_valuechange)
        topics.default_description.subscribe(self._ev_defaultvaluechange)
        topics.text_description.subscribe(self._ev_textchange)

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))

    @property
    def value(self) -> Dict[str, str]:
        return self._value

    @value.setter
    def value(self, value: Dict[str, Any]) -> None:
        if not value and self.default_value:
            self.value = self.default_value
            return

        self._value = value
        default = dict(
            title="",
            subtitle="",
            text="",
            img="",
            interactions=[]
        )
        value = {**default, **value}

        image = self.childs['img']
        text = self.childs['text']
        interactions = self.childs['interactions']
        self.childs['title'].value = value['title']
        self.childs['subtitle'].value = value['subtitle']
        text.value = value['text']

        image.style.display = Display.NONE
        interactions.style.display = Display.NONE
        if value['interactions']:
            interactions.display_interactions(value['interactions'])
            text.style.y = 15
            interactions.style.width = self.geometry.content_width
            interactions.style.height = 12
            interactions.style.display = Display.INITIAL
        elif value['img']:
            image.value = value['img']
            text.style.y = self.geometry.content_width
            image.style.width = self.geometry.content_width
            image.style.height = self.geometry.content_width
            image.style.display = Display.INITIAL
        else:
            text.style.y = 4

    def _ev_valuechange(self, args: Dict[str, Any] = None) -> None:
        self.value = args

    def _ev_defaultvaluechange(self, args: Dict[str, Any] = None) -> None:
        self.default_value = args

    def _ev_textchange(self, value: Any) -> None:
        self.childs["text"].value = value


class Opportunity(BaseMouseFocusable):
    def __init__(self, value: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

        def ev_mousefocusgain(ev: tcod.event.MouseMotion, op=self) -> None:
            topics.text_description.publish(value="\t{:c}{:c}{:c}{:c}{}{:c}".format(
                tcod.COLCTRL_FORE_RGB, *(200, 200, 0),
                data.interactions[self.value]['long_desc'], tcod.COLCTRL_STOP))

        def ev_mousefocuslost(ev: tcod.event.MouseMotion, op=self) -> None:
            topics.text_description.publish(value="")

        self.focus_dispatcher.ev_mousefocusgain.append(ev_mousefocusgain)
        self.focus_dispatcher.ev_mousefocuslost.append(ev_mousefocuslost)

        logger.debug("new {}: {}", Opportunity.__name__, repr(self))

    def update(self):
        self.should_update = False

    def base_drawing(self):
        super().base_drawing()
        self.console.print(
            0, 0, data.interactions[self.value]['short_desc'])


class InteractionsPanel(Canvas):
    def __init__(self, *args, interactions: List[str] = list(), **kwargs):
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)
        self.display_interactions(interactions)

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))

    def display_interactions(self, interactions: List[str]) -> None:
        self.childs.clear()
        for i, opportunity in enumerate(sorted(interactions)):
            style = dict(x=3, y=i+3, height=1,
                         width=self.geometry.content_width-3, bg_alpha=0)
            focused_style = dict(fg_color=(200, 200, 0))

            def op_maker(op_=opportunity):
                return Opportunity(op_, style=style, focused_style=focused_style)
            self.childs.add(op_maker())
        self.force_redraw = True

    def base_drawing(self) -> None:
        super().base_drawing()
        self.console.print(0, 0, "Opportunity list:")
        for i in range(len(self.childs)):
            self.console.print(1, i+3, f"{i+1}.")
        self.console.bg[2:len(self.childs)+4, :] = (20,)*3


class LeftPanel(Canvas):
    def __init__(self, *args, **kwargs):
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)
        log_style = dict(y=1., width=1., height=.5, bg_color=(20,)*3,
                         origin=Origin.BOTTOM_LEFT, border=Border.EMPTY,
                         border_bg_color=(0,)*3)
        # choice_style = dict(y=0, width=1., height=0,
        #                     bg_color=(50, 200, 50),
        #                     origin=Origin.BOTTOM_LEFT)
        description_style = dict(width=1.0, height=1., bg_color=(89, 254, 42),
                                 key_color=(89, 254, 42))

        # starting_value = dict(title="Welcome", subtitle="Here goes subtitle",
        #                       text="Some text here !", img="")

        description_screen = DescriptionPanel({}, name="description",
                                              style=description_style)
        log_screen = LogUI(name="log", style=log_style)
        # choice_screen = InteractionsScreen(style=choice_style)

        self.childs.add(log_screen, description_screen)

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))


class MainScreen(Canvas):
    def __init__(self, country: Country, *args, **kwargs):
        logger.debug("{} initialisation started", __class__.__name__)
        super().__init__(*args, **kwargs)

        self.country = country

        characters_style = dict(x="1.+1", y=-1, width=10, height="1.+2",
                                bg_color=tcod.black, key_color=(100, 254, 1),
                                origin=Origin.TOP_RIGHT, border=Border.DOUBLE,
                                border_fg_color=(100,)*3)
        left_panel_style = dict(x=-1, y=-1, width=26,
                                height='1.+2', border=Border.DOUBLE,
                                border_fg_color=(100,)*3)

        loc_width = f"-{left_panel_style['width']+characters_style['width']-2}+1."
        top_info_width = f"-{left_panel_style['width']+characters_style['width']-2}+1."

        top_info_bar = dict(x=left_panel_style['width']-1, width=top_info_width,
                            height=2, bg_color=(0, 20, 20))

        loc_height = f"-{top_info_bar['height']}+1."
        location_style = dict(x=left_panel_style['width']-1, y=top_info_bar['height'],
                              width=loc_width, height=loc_height,
                              bg_color=(0, 20, 20))

        left_panel_screen = LeftPanel(name="left_panel", style=left_panel_style)
        char_screen = CharactersPanel(name="characters",
                                      style=characters_style)
        info_screen = InfosPanel(style=top_info_bar)
        location = Location(country, "standard", (10, 10))
        location_ui = LocationUI(location, name="location",
                                 style=location_style)
        self.childs.add(left_panel_screen, info_screen,
                        char_screen, location_ui)

        left_panel_screen.childs['description'].value = info_screen.description
        starting_position = location.player_position
        area_desc = location_ui.childs[str(starting_position)].description
        left_panel_screen.childs['description'].default_value = area_desc

        logger.debug("{} initialisation done: {}",
                     __class__.__name__, repr(self))


def main() -> None:
    def handle_events(root_canvas: RootCanvas) -> None:
        events = tcod.event.get()
        for event in events:
            if event.type == "QUIT":
                raise SystemExit()
            if event.type == "KEYDOWN" and event.sym == tcod.event.K_ESCAPE:
                raise SystemExit()
            root_canvas.handle_focus_event(event)

    import logging.config
    import yaml
    with open("logconfig.yml") as f:
        configdict = yaml.load(f, Loader=yaml.FullLoader)
    logging.config.dictConfig(configdict)
    logging.debug("test %s", __name__)

    country = Country("BlueLand", mood=-200)

    # flag = tcod.FONT_LAYOUT_TCOD | tcod.FONT_TYPE_GREYSCALE
    # tcod.console_set_custom_font("data/fonts/dejavu10x10_gs_tc.png", flag)
    # res_w, res_h = tcod.sys_get_current_resolution()
    # char_w, char_h = tcod.sys_get_char_size()
    # root_w = res_w // char_w
    # root_h = res_h // char_h
    root_w = 80
    root_h = 50
    root_canvas = RootCanvas(root_w, root_h, "room maze",
                             "data/fonts/dejavu10x10_gs_tc.png",
                             renderer=tcod.RENDERER_OPENGL2,
                             fullscreen=False)
    main_screen = MainScreen(country=country, style=dict(width=1., height=1.))
    char_list = [Character() for _ in range(6)]

    main_screen.childs["characters"].characters = char_list

    # location = Location("standard", 10, 10, style=dict(width=1., height=1.))

    root_canvas.childs.add(main_screen)

    # root_canvas.update_kbd_focus()

    tcod.sys_set_fps(60)
    while True:
        root_canvas.refresh()
        tcod.console_flush()
        handle_events(root_canvas)


if __name__ == "__main__":
    main()
