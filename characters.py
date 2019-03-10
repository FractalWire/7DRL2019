from __future__ import annotations
import os
import json
from enum import Enum, IntFlag, auto
from typing import Tuple, Dict, Any
import random as rnd
import tcod
from common import Alignment, align_index, ranks, professions, img_dir
from common import colored_alignment_str


class Wound(IntFlag):
    LIGHT = auto()
    HEAVY = auto()
    DISABLE = auto()


################
# RANKS HELPER #
################


def get_rank(juice: int) -> Dict[str, Any]:
    for k, v in ranks.items():
        lower, upper = v["bounds"]
        if lower is None:
            if juice < upper:
                return v
        elif upper is None:
            if juice >= lower:
                return v
        elif lower <= juice < upper:
            return v


def rank_str(juice: int, alignment: Alignment) -> str:
    align = align_index(alignment)
    rank = get_rank(juice)
    return " ".join(w for w in [rank["preposition"][align],
                                rank["short_desc"][align]] if w)


####################
# ALIGNMENT HELPER #
####################


alignment_str = {Alignment.CONSERVATIVE: "Conservative",
                 Alignment.MODERATE: "Moderate",
                 Alignment.LIBERAL: "Liberal",
                 Alignment.ANY: "Without convictions"}


def alignment_mod(alignment: Alignment) -> Dict[str, Tuple[int, int]]:
    if alignment == Alignment.CONSERVATIVE:
        a_mod = dict(heart=(-10, -5), wisdom=(10, 5))
    elif alignment == Alignment.MODERATE:
        a_mod = dict()
    elif alignment == Alignment.LIBERAL:
        a_mod = dict(heart=(10, 5), wisdom=(-10, -5))
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


def profession_mod(prof_name: str) -> Dict[str, Tuple[int, int]]:
    if "attrs_mod" in professions[prof_name]:
        return professions[prof_name]["attrs_mod"]
    return {}


def profession_align(prof_name: str) -> Alignment:
    return Alignment[professions[prof_name]["alignment"].upper()]


def profession_juice(prof_name: str) -> int:

    if "juice" not in professions[prof_name]:
        return 0
    juice = professions[prof_name]["juice"]
    if isinstance(juice, int):
        return juice
    # assume list here
    lower, upper = juice
    return rnd.randrange(lower, upper)


class Sex(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class Attributes:
    def __init__(self, attributes={}, **kwargs):
        self.hp = 1,
        self.heart = 1,
        self.wisdom = 1,
        self.intel = 1,
        self.strength = 1,
        self.agility = 1,
        self.charisma = 1
        with open("data/attributes.json") as f:
            self._meta = json.load(f)
        attributes = {**attributes, **kwargs}
        for k, v in attributes.items():
            if k not in self.__dict__:
                raise KeyError(f"{k} is not a valid attribute")
            setattr(self, k, v)

    def __str__(self):
        return "\n".join(f"{self._meta[k]['short_desc']:<13}:{v:>3}"
                         for k, v in self.__dict__.items() if k[0] != "_")

    def juicy(self, juice: int, align: Alignment) -> Attributes:
        rank = get_rank(juice)
        ind = rank["ind"]
        if ind == 0:
            return Attributes()
        base_rank = 3
        if ind < base_rank:
            juice_mod = 1/4
        else:
            juice_mod = 1/6

        d = {}
        for k, attr in self.__dict__.items():
            if k[0] != "_":
                d[k] = max(1, int(attr*(1+(ind-base_rank)*juice_mod)))
        if align == Alignment.CONSERVATIVE:
            d["heart"] = self.heart
        elif align == Alignment.LIBERAL:
            d["wisdom"] = self.wisdom

        return Attributes(d)

    @classmethod
    def random(cls, align_mod: Dict[str, Tuple[int, int]] = {},
               prof_mod: Dict[str, Tuple[int, int]] = {},
               mood_mod: Dict[str, Tuple[int, int]] = {}) -> Attributes:
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
        for k, v in mood_mod.items():
            attrs_range[k] = tuple(a+b for a, b in zip(attrs_range[k], v))
        for k, v in align_mod.items():
            attrs_range[k] = tuple(a+b for a, b in zip(attrs_range[k], v))
        for k, v in prof_mod.items():
            attrs_range[k] = tuple(a+b for a, b in zip(attrs_range[k], v))

        attributes = {k: rnd.randrange(max(1, v[0]), max(2, v[0]+1, v[1]))
                      for k, v in attrs_range.items()}

        return cls(attributes)


tcod.namegen_parse('data/names/name_tcod_structures.dat')


class Character:
    def __init__(self, name: str = "", surname: str = "", nickname: str = "",
                 sex: Sex = None, img="", attributes=None, alignment: Alignment = None,
                 prof_name="civilian", juice: int = 0, mood_mod: Dict[str, int] = {},
                 inventory=()) -> None:
        self.sex = sex or rnd.choice(
            [Sex.MALE.value, Sex.FEMALE.value])
        tmp_sex = self.sex if self.sex != Sex.UNKNOWN else rnd.choice(
            [Sex.MALE.value, Sex.FEMALE.value])
        self.name = name or tcod.namegen_generate_custom(tmp_sex, "$s")
        self.surname = surname or tcod.namegen_generate_custom(tmp_sex, "$e")
        self.nickname = nickname or tcod.namegen_generate("animal").title()
        self.age = rnd.choices([rnd.randrange(16, 21), rnd.randrange(21, 40),
                                rnd.randrange(40, 80)], [15, 70, 15])[0]
        self.img = img or rnd.choice(os.listdir(f"data/img/{self.sex}"))
        self.profession = prof_name
        p_mod = profession_mod(self.profession)
        # self.alignment = alignment or profession_align(self.profession)
        born_align = alignment or profession_align(self.profession)
        a_mod = alignment_mod(born_align)
        self.attributes = attributes or Attributes.random(a_mod, p_mod,
                                                          mood_mod)
        self.inventory = inventory
        self.juice = juice or profession_juice(self.profession)
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

    @property
    def img_path(self) -> str:
        return f"{img_dir}/{self.sex}/{self.img}"

    @property
    def description(self) -> Dict[str, str]:
        rank_str = f"{get_rank(self.juice)['short_desc'][align_index(self.alignment)].upper()}"
        rank_str = colored_alignment_str(self.alignment, rank_str)
        prof_str = f"{self.profession.capitalize()}"
        age_str = f"Age {self.age}, {self.sex.capitalize()}"
        juice_str = f"Juice: {self.juice}"

        attrs_str = str(self.attributes.juicy(self.juice, self.alignment))
        text = f"{age_str}\n{prof_str}\n\n{rank_str}\n{juice_str}\n\n{attrs_str}"
        nick = "aka "+self.nickname if self.nickname else ""

        return dict(title=self.fullname, subtitle=nick, text=text,
                    img=self.img_path)

    @property
    def colored_profession(self) -> str:
        return colored_alignment_str(self.alignment, self.profession)

    def __repr__(self):
        return professions[self.profession]["short_desc"]

    def __str__(self):
        true_align = real_alignment(self.attributes)
        true_align_str = alignment_str[true_align]
        prof_align_str = alignment_str[profession_align(self.profession)]
        align_str = (f"Was born {prof_align_str.upper()}, but "
                     f"{true_align_str.upper()} is his/her true nature")
        prof_str = f"Profession: {self.profession.upper()}"
        juice_str = (f"He/She has {self.juice} juice and is therefore considered"
                     f" {rank_str(self.juice, true_align).upper()} by society.")
        attrs_str = '\n\t'.join(
            str(self.attributes.juicy(self.juice, self.alignment)).split('\n'))

        return (f"{type(self).__name__} {self.fullname} is a {self.age} y.o. {self.sex}:\n"
                f"\t{self.img}\n"
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
