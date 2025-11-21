from dataclasses import dataclass


@dataclass
class GeomVaseOutline:
    """
    Grammar-of-graphics geom that indicates vase overlays should be applied
    on cube faces during viewer rendering.
    """

    color: str = "limegreen"
    alpha: float = 0.6
