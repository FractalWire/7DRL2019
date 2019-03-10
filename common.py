from __future__ import annotations
import tcod
import json
from enum import IntFlag, auto

img_dir = "data/img"

portrait_size = 256

with open('data/ranks.json') as f:
    ranks = json.load(f)

with open("data/professions.json") as f:
    professions = json.load(f)

with open("data/locations.json") as f:
    locations = json.load(f)

with open('data/areas.json') as f:
    areas = json.load(f)

with open('data/interactions.json') as f:
    interactions = json.load(f)


class Alignment(IntFlag):
    ARCHCONSERVATIVE = auto()
    CONSERVATIVE = auto()
    MODERATE = auto()
    LIBERAL = auto()
    ELITELIBERAL = auto()
    ANY = ARCHCONSERVATIVE | CONSERVATIVE | MODERATE | LIBERAL | ELITELIBERAL


alignment_color = {Alignment.CONSERVATIVE: (255, 0, 0),
                   Alignment.MODERATE: (255, 255, 0),
                   Alignment.LIBERAL: (0, 255, 0),
                   Alignment.ANY: (255, 255, 255)}


def colored_alignment_str(alignment: Alignment, s: str) -> str:
    color = alignment_color[alignment]
    return "{:c}{:c}{:c}{:c}{}{:c}".format(tcod.COLCTRL_FORE_RGB, *color, s,
                                           tcod.COLCTRL_STOP)


def std_align(align) -> Alignment:
    if align & Alignment.ARCHCONSERVATIVE:
        return Alignment.CONSERVATIVE
    if align & Alignment.ELITELIBERAL:
        return Alignment.LIBERAL
    return align


# TODO: int_align not great...
_int_align = [Alignment.CONSERVATIVE, Alignment.MODERATE, Alignment.LIBERAL]


def align_index(align) -> int:
    for i, v in enumerate(_int_align):
        if v & std_align(align):
            return i


# format (repr, isviolent, offence_score)
offences = dict(
    propaganda=("Propaganda", False, 1),
    vandalism=("Vandalism", True, 2),
    nudity=("Public nudity", False, 2),
    speech=("Harmful speech", False, 3),
    theft=("Theft", False, 3),
    drug=("Drug dealing", False, 4),
    assault=("Assault", True, 5),
    murder=("Murder", True, 10),
    flag=("Flag burning", False, 10)
)
