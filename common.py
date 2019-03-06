from enum import IntFlag, auto


class Alignment(IntFlag):
    ARCHCONSERVATIVE = auto()
    CONSERVATIVE = auto()
    MODERATE = auto()
    LIBERAL = auto()
    ELITELIBERAL = auto()
    ANY = ARCHCONSERVATIVE | CONSERVATIVE | MODERATE | LIBERAL | ELITELIBERAL


def std_align(align) -> Alignment:
    return align & ~(Alignment.ARCHCONSERVATIVE | Alignment.ELITELIBERAL)


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
