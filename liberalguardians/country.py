from datetime import date
from typing import Dict
from enum import IntEnum

from liberalguardians.characters import Character
from liberalguardians.common.alignment import Alignment, std_align
from liberalguardians.common.alignment import colored_alignment_str


class Speed(IntEnum):
    VERYSLOW = 1
    SLOW = 2
    NORMAL = 4
    FAST = 6
    VERYFAST = 12


MOOD_MIN = -1000
MOOD_MAX = 1000

alignment_country_str = {Alignment.ARCHCONSERVATIVE: "fanatically conservative",
                         Alignment.CONSERVATIVE: "strongly conservative",
                         Alignment.MODERATE: "susceptible to liberal ideas",
                         Alignment.LIBERAL: "showing liberal sympathy",
                         Alignment.ELITELIBERAL: "embracing liberal ideas"}


class Country:
    def __init__(self, name, mood: int = MOOD_MIN, start: date = None,
                 speed: int = Speed.NORMAL) -> None:
        self.name = name
        self._mood = mood
        self.start = start or date.today()
        self.time = self.start
        self.president = Character(prof_name="president",
                                   alignment=self.std_alignment)

    @property
    def description(self) -> Dict[str, str]:
        title = colored_alignment_str(self.std_alignment, self.name)
        subtitle = self.time.strftime("%B %Y")
        align_str = "The country is {}".format(
            colored_alignment_str(self.std_alignment, alignment_country_str[self.alignment]))
        president = self.president
        president_str = "The current president is: {}".format(
            colored_alignment_str(president.alignment, president.fullname))
        text = "{}\n\n{}\n".format(align_str, president_str)

        return dict(title=title, subtitle=subtitle, text=text)

    @property
    def mood(self) -> int:
        return self._mood

    @mood.setter
    def mood(self, value: int) -> None:
        self._mood = value
        self._mood = sorted([-1000, self._mood, 1000])[0]

    @property
    def mood_modifier(self) -> Dict[str, int]:
        mod = round(self.mood/MOOD_MAX*5)
        return dict(heart=(mod, mod), wisdom=(-mod, -mod))

    @property
    def alignment(self) -> Alignment:
        bounds = {
            Alignment.ARCHCONSERVATIVE: [-1000, -750],
            Alignment.CONSERVATIVE: [-750, -250],
            Alignment.MODERATE: [-250, 250],
            Alignment.LIBERAL: [250, 750],
            Alignment.ELITELIBERAL: [750, 1000],
        }
        for k, v in bounds.items():
            if v[0] <= self.mood <= v[1]:
                return k

    @property
    def std_alignment(self) -> Alignment:
        return std_align(self.alignment)
