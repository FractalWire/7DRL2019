from enum import IntFlag, auto
import tcod


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


def align_index(align) -> int:
    if align & (Alignment.CONSERVATIVE | Alignment.ARCHCONSERVATIVE):
        return 0
    if align & Alignment.MODERATE:
        return 1
    if align & (Alignment.LIBERAL | Alignment.ELITELIBERAL):
        return 2
