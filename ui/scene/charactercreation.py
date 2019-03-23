import tcod
from tcodplus.canvas import Canvas, RootCanvas
from tcodplus.widgets import Header, Button, Text
from tcodplus.style import Border, Origin
from characters import Character, Sex


class AttributesPanel(Canvas):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def base_drawing(self) -> None:
        super().base_drawing()
        attrs = self.parent.char.attributes
        for i, attr in enumerate(str(attrs).split('\n')):
            self.console.print(1, 1+2*i, str(attr))


class CharacterCreationScreen(Canvas):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.char = Character(prof_name="activist")
        self.lore_str = ("\nThe following individual was recently monitored by "
                         "our service.\n\nIt appears this individual strongly "
                         "believes in seditious liberal ideas. At the moment, "
                         "the individual poses no threat, but the service "
                         "recommend to keep a close eye on the individual.")
        title_bar = Header("Intelligence report", style=dict(
            width=1., height=3, bg_color=(20, 20, 100)))
        pic_style = dict(x=1., y=4, width=10, height=13, bg_color=(240, 240, 240),
                         fg_color=(100, 100, 100), origin=Origin.TOP_RIGHT,
                         border=Border.PATTERN1, border_bg_color=(220, 220, 220))
        picture = Header("No recorded picture", style=pic_style)

        lore_style = dict(x=0, y=4, width=f"-{pic_style['width']}+1.",
                          height=13, max_width=None, border=Border.DASHED,
                          bg_color=self.style.bg_color, fg_color=(100, 100, 100))
        lore = Text(self.lore_str, style=lore_style)

        tick_focused_style = dict(fg_color=(30, 30, 140))
        sex_style = dict(y=18, border=Border.SOLID, bg_color=tcod.white,
                         fg_color=tcod.black)
        male_button = Button(" ", name=Sex.MALE.value, style={**sex_style, "x": 7},
                             focused_style=tick_focused_style)
        female_button = Button(" ", name=Sex.FEMALE.value, style={**sex_style, "x": 17},
                               focused_style=tick_focused_style)
        unknown_button = Button(" ", name=Sex.UNKNOWN.value, style={**sex_style, "x": 28},
                                focused_style=tick_focused_style)

        sex_but_list = [male_button, female_button, unknown_button]
        but_cnt = len(sex_but_list)
        self.sex_info = ""
        for but_ind in range(but_cnt):
            def ev_mousebuttondown(ev: tcod.event.MouseButtonDown,
                                   but_ind=but_ind) -> None:
                sex_but_list[but_ind].value = 'X'
                self.char.sex = sex_but_list[but_ind].name
                for i in range(but_cnt):
                    if i != but_ind:
                        sex_but_list[i].value = " "
            sex_but_list[but_ind].focus_dispatcher.ev_mousebuttondown.append(ev_mousebuttondown)

        path_style = dict(y=33, border=Border.SOLID, bg_color=tcod.white,
                          fg_color=tcod.black)
        money_button = Button(" ", style={**path_style, "x": 7},
                              focused_style=tick_focused_style)
        fame_button = Button(" ", style={**path_style, "x": 17},
                             focused_style=tick_focused_style)
        power_button = Button(" ", style={**path_style, "x": 28},
                              focused_style=tick_focused_style)

        self.money = 100
        self.attributes_pool = 10
        self.followers = 0
        path_but_list = [money_button, fame_button, power_button]
        but_cnt = len(path_but_list)
        path_but_mod = [["money", 100, 1000], ["attributes_pool", 10, 15],
                        ["followers", 0, 2]]
        for but_ind in range(but_cnt):

            def ev_mousebuttondown(ev: tcod.event.MouseButtonDown,
                                   but_ind: int = but_ind) -> None:
                path_but_list[but_ind].value = 'X'
                for i in range(but_cnt):
                    attr, base, plus = path_but_mod[i]
                    setattr(self, attr, plus)
                    if i != but_ind:
                        path_but_list[i].value = " "
                        setattr(self, attr, base)
            path_but_list[but_ind].focus_dispatcher.ev_mousebuttondown.append(
                ev_mousebuttondown)

        attrs_style = dict(x=0, y=46, width=.52, height=17,
                           bg_color=(240, 240, 240), fg_color=(100, 100, 100),
                           border=Border.PATTERN1, border_bg_color=(220, 220, 220))
        attrs_panel = AttributesPanel(style=attrs_style)

        crime_style = dict(x=1., y=46, width=.5, height=17, bg_color=(240, 240, 240),
                           fg_color=(100, 100, 100), origin=Origin.TOP_RIGHT,
                           border=Border.PATTERN1, border_bg_color=(220, 220, 220))
        crime_records = Header("No known criminal activity", style=crime_style)

        send_style = dict(x=.95, y="-1+1.", origin=Origin.BOTTOM_RIGHT,
                          border=Border.EMPTY, border_fg_color=(50,)*3,
                          bg_color=(20, 20, 100), fg_color=(200,)*3)
        send_button = Button("SEND REPORT", style=send_style,
                             focused_style=dict(bg_color=(30, 30, 140)))

        self.childs.add(title_bar, lore, picture, male_button, female_button,
                        unknown_button, money_button, fame_button, power_button,
                        attrs_panel, crime_records, send_button)

    def base_drawing(self) -> None:
        super().base_drawing()
        self.console.ch[3, :] = 205  # double line
        w = self.geometry.content_width
        field_value_str = (
            f"{'male':>13}{'female':>12}{'unknown':>12}\n\n\n"
            f"{self.char.name:.>{w-2}}\n\n"
            f"{self.char.surname:.>{w-2}}\n\n"
            f"{'':.>{w-2}}\n\n"
            f"{self.char.age:.>{w-2}}\n\n"
            f"{'Political Activist':.>{w-2}}\n\n\n"
        )
        self.console.print(1, 19, field_value_str)
        field_str = (
            "Sex :\n\n\n"
            "First Name:\n\n"
            "Surname:\n\n"
            "Known as:\n\n"
            "Age:\n\n"
            "Profession:\n\n\n"
        ).upper()
        self.console.print(1, 19, field_str)

        self.console.fg[32, 1:-1] = (180,)*3
        self.console.ch[32, 1:-1] = 196  # solid line

        path_value_str = (
            f"{'money':>14}{'fame':>9}{'power':>12}\n\n\n"
            f"{self.money:.>{w-2}}\n\n"
            f"{self.followers:.>{w-2}}\n\n"
        )
        self.console.print(1, 34, path_value_str)
        path_str = (
            "Path:\n\n\n"
            "Funds:\n\n"
            "Followers:\n\n\n\n"
        ).upper()
        self.console.print(1, 34, path_str)

        self.console.fg[41, 1:-1] = (180,)*3
        self.console.ch[41, 1:-1] = 196  # solid line

        self.console.print(0, 43,
                           f"{'Attributs:'.upper():>{w//4+6}} {self.attributes_pool:02}")
        self.console.print(w//2, 43, f"{'Criminal records:'.upper():>{w//4+8}}")


def main():
    font = "data/fonts/dejavu10x10_gs_tc.png"
    root_canvas = RootCanvas(100, 70, "setup screen tests", font,
                             renderer=tcod.RENDERER_OPENGL)

    def handle_events(root_canvas: RootCanvas) -> None:
        for event in tcod.event.get():
            if event.type == "KEYDOWN" and event.sym == tcod.event.K_ESCAPE:
                raise SystemExit()
            root_canvas.handle_focus_event(event)

    style = dict(x=.25, width=.5, height=1., bg_color=tcod.white,
                 fg_color=tcod.black, border=Border.PATTERN2,
                 border_bg_color=(40, 40, 100))
    char_canvas = CharacterCreationScreen(style=style)

    root_canvas.childs.add(char_canvas)

    tcod.sys_set_fps(60)
    while not tcod.console_is_window_closed():
        root_canvas.refresh()
        tcod.console_flush()
        handle_events(root_canvas)


if __name__ == "__main__":
    main()
