from __future__ import annotations
import json
from enum import Enum, IntFlag, auto
from typing import Tuple, Dict
import random as rnd
import tcod
from common import Alignment, align_index


class Wound(IntFlag):
    LIGHT = auto()
    HEAVY = auto()
    DISABLE = auto()


################
# RANKS HELPER #
################

with open('data/ranks.json') as f:
    ranks = json.load(f)


def rank_str(juice: int, alignment: Alignment) -> str:
    align = align_index(alignment)
    for k, v in ranks.items():
        lower, upper = v["bounds"]
        if lower is None:
            if juice < upper:
                return " ".join(w for w in [v["preposition"][align],
                                            v["str"][align]] if w)
        elif upper is None:
            if juice >= lower:
                return " ".join(w for w in [v["preposition"][align],
                                            v["str"][align]] if w)
        else:
            if lower <= juice < upper:
                return " ".join(w for w in [v["preposition"][align],
                                            v["str"][align]] if w)


####################
# ALIGNMENT HELPER #
####################


alignment_str = {Alignment.CONSERVATIVE: "Conservative",
                 Alignment.MODERATE: "Moderate",
                 Alignment.LIBERAL: "Liberal",
                 Alignment.ANY: "Without convictions"}


def alignment_mod(alignment: Alignment) -> Dict[str, Tuple[int, int]]:
    if alignment == Alignment.CONSERVATIVE:
        a_mod = dict(heart=(-5, -5), wisdom=(5, 5))
    elif alignment == Alignment.MODERATE:
        a_mod = dict()
    elif alignment == Alignment.LIBERAL:
        a_mod = dict(heart=(5, 5), wisdom=(-5, -5))
    else:  # Alignment.ANY
        a_mod = dict()  # insert world's influence here

    return a_mod


def real_alignment(attrs: Attributes) -> Alignment:
    heart, wisdom = attrs.heart, attrs.wisdom
    balance = heart-wisdom
    if balance < -2:
        return Alignment.CONSERVATIVE
    elif balance > 2:
        return Alignment.LIBERAL
    else:
        return Alignment.MODERATE


######################
# PROFESSIONS HELPER #
######################
with open("data/professions.json") as f:
    professions = json.load(f)


def profession_mod(prof_name: str) -> Dict[str, Tuple[int, int]]:
    return professions[prof_name]["attrs_mod"]


def profession_align(prof_name: str) -> Alignment:
    return Alignment[professions[prof_name]["alignment"].upper()]


class Sex(Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"


class Attributes:
    def __init__(self, attributes={}, **kwargs):
        default = dict(
            hp=8,
            heart=8,
            wisdom=8,
            intel=8,
            strength=8,
            agility=8,
            charisma=8
        )
        attributes = {**default, **attributes, **kwargs}
        for k, v in attributes.items():
            if k not in default:
                raise KeyError(f"{k} is not a valid attribute")
            setattr(self, k, v)

    def __str__(self):
        attr_str = "\n\t".join(f"{k:<9}:{v:>3}" for k,
                               v in self.__dict__.items())
        return (f"{type(self).__name__}:\n"
                f"\t{attr_str}")

    @classmethod
    def random(cls, alignment_mod: Dict[str, Tuple[int, int]] = {},
               profession_mod: Dict[str, Tuple[int, int]] = {}) -> Attributes:
        default = dict(
            hp=(0, 10),
            heart=(0, 10),
            wisdom=(0, 10),
            intel=(0, 10),
            strength=(0, 10),
            agility=(0, 10),
            charisma=(0, 10)
        )

        attrs_range = {**default}
        for k, v in alignment_mod.items():
            attrs_range[k] = tuple(a+b for a, b in zip(attrs_range[k], v))
        for k, v in profession_mod.items():
            attrs_range[k] = tuple(a+b for a, b in zip(attrs_range[k], v))

        attributes = {k: rnd.randrange(max(1, v[0]), max(2, v[0]+1, v[1]))
                      for k, v in attrs_range.items()}

        return cls(attributes)


tcod.namegen_parse('data/names/name_tcod_structures.dat')


class Character:
    def __init__(self, name: str = "", surname: str = "", nickname: str = "",
                 sex: Sex = None, attributes=None, alignment: Alignment = None,
                 prof_name="civilian", juice: int = 0, inventory=()) -> None:
        self.sex = sex or rnd.choice(
            [Sex.MALE.value, Sex.FEMALE.value])
        tmp_sex = self.sex if self.sex != Sex.UNKNOWN else rnd.choice(
            [Sex.MALE.value, Sex.FEMALE.value])
        self.name = name or tcod.namegen_generate_custom(tmp_sex, "$s")
        self.surname = surname or tcod.namegen_generate_custom(tmp_sex, "$e")
        self.nickname = nickname
        self.age = rnd.choices([rnd.randrange(16, 21), rnd.randrange(21, 40),
                                rnd.randrange(40, 80)], [15, 70, 15])[0]
        self.profession = prof_name
        p_mod = profession_mod(self.profession)
        # self.alignment = alignment or profession_align(self.profession)
        born_align = alignment or profession_align(self.profession)
        a_mod = alignment_mod(born_align)
        self.attributes = attributes or Attributes.random(a_mod, p_mod)
        self.inventory = inventory
        self.juice = juice or rnd.randrange(-100, 1100)  # to polish
        self.offence = {}
        self.wounds = {}
        self.followers = []

    @property
    def fullname(self) -> str:
        return " ".join([self.name, self.surname])

    @property
    def alignment(self) -> Alignment:
        heart, wisdom = self.attributes.heart, self.attributes.wisdom
        balance = heart-wisdom
        if balance < -2:
            return Alignment.CONSERVATIVE
        elif balance > 2:
            return Alignment.LIBERAL
        else:
            return Alignment.MODERATE

    def __str__(self):
        true_align = real_alignment(self.attributes)
        true_align_str = alignment_str[true_align]
        prof_align_str = alignment_str[profession_align(self.profession)]
        align_str = (f"Was born {prof_align_str.upper()}, but "
                     f"{true_align_str.upper()} is his/her true nature")
        prof_str = f"Profession: {self.profession.upper()}"
        juice_str = (f"He/She has {self.juice} juice and is therefore considered"
                     f" {rank_str(self.juice, true_align).upper()} by society.")
        attrs_str = '\n\t'.join(str(self.attributes).split('\n'))

        return (f"{type(self).__name__} {self.fullname} is a {self.age} y.o. {self.sex}:\n"
                f"\t{align_str}\n"
                f"\t{prof_str}\n"
                f"\t{juice_str}\n"
                f"\t{attrs_str}")


def main() -> None:

    for k in professions:
        c = Character(prof_name=k)
        print(c)
        print()


if __name__ == "__main__":
    main()
