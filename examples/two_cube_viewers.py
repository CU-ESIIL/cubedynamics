"""Quick regression script to render two independent CubePlot viewers.

Run this file in a notebook cell or with ``python examples/two_cube_viewers.py``
to emit two HTML snippets back-to-back. Each viewer should have a unique DOM id
and manipulating one should not reset the other in notebook outputs.
"""

import numpy as np
import xarray as xr

from cubedynamics.plotting import CubePlot


def make_cube(seed: int, name: str) -> xr.DataArray:
    rng = np.random.default_rng(seed)
    data = rng.random((3, 4, 4))
    return xr.DataArray(
        data,
        dims=("time", "y", "x"),
        name=name,
        attrs={"description": f"demo cube {name}"},
    )


def main() -> None:
    first = CubePlot(make_cube(0, "first"))
    second = CubePlot(make_cube(1, "second"))

    html_a = first._repr_html_()
    html_b = second._repr_html_()

    with open("two_cube_viewers.html", "w", encoding="utf-8") as f:
        f.write(html_a)
        f.write("\n\n")
        f.write(html_b)

    print("Wrote two_cube_viewers.html with two independent viewers.")


if __name__ == "__main__":
    main()
