from __future__ import annotations
import logging
from typing import Tuple, List, TYPE_CHECKING
import random as rnd

from liberalguardians.common.logging import StyleAdapter
import liberalguardians.common.data as data
from liberalguardians.characters import Character
# import numpy as np

if TYPE_CHECKING:
    from location import Location

logger = StyleAdapter(logging.getLogger(__name__))
_professions_list = list(data.professions)


class Area:
    def __init__(self, location: Location, coordinates: Tuple[int, int],
                 area_name: str, characters: List[Character] = list()) -> None:
        self.location = location
        self.coordinates = coordinates

        self.area_name = area_name
        self.characters = characters

    def randomize(self) -> None:
        country = self.location.country
        encounter_cnt = rnd.randrange(10, 20)

        characters = []
        for _ in range(encounter_cnt):
            encounter = data.areas[self.area_name]["encounter"]
            weight_sum = sum(encounter.values())
            any_weight = 10 - weight_sum
            if any_weight > 0:
                encounter["any"] = any_weight
            encounter_choice = rnd.choices(*zip(*encounter.items()))[0]
            if encounter_choice == "any":
                encounter_choice = rnd.choice(_professions_list)
            characters.append(Character(prof_name=encounter_choice,
                                        mood_mod=country.mood_modifier))
        self.characters = characters
        logger.debug("{} randomized".format(repr(self)))

    # @classmethod
    # def random(cls, area_name: str) -> Area:
    #     area = cls(area_name)
    #     area.randomize()

    #     return area

    def __repr__(self):
        s = (f"{data.areas[self.area_name]['short_desc'].title()} with "
             f"{len(self.characters)} people")
        return s

    def __str__(self):
        characters_str = '\n\t'.join(repr(c) for c in self.characters)
        s = f"{repr(self)} :\n\t{characters_str}"
        return s
