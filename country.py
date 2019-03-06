from datetime import date
from enum import IntEnum
from characters import Character
from common import Alignment, std_align


class Speed(IntEnum):
    VERYSLOW = 1
    SLOW = 2
    NORMAL = 4
    FAST = 6
    VERYFAST = 12


class Country:
    def __init__(self, name, mood: int = -1000, start: date = None,
                 speed: int = Speed.NORMAL) -> None:
        self.name = name
        self._mood = mood
        self.start = start or date.today()
        self.president = Character(profession="president",
                                   alignment=std_align(self.alignment))

    @property
    def mood(self) -> int:
        return self._mood

    @mood.setter
    def mood(self, value: int) -> None:
        self._mood = (value/abs(value)) * (min(abs(value), 1000))

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
            if v[0] < self.mood <= v[1]:
                return k
