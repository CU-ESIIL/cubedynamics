"""Generate a Ghosh-style tail-association figure for climate synchrony."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from cubedynamics.plotting import (
    plot_tail_association_from_cube,
    plot_tail_association_grid,
    tail_association_stats,
)


def synthetic_tail_pairs(seed: int = 8, n: int = 180) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """Return mirrored pairs with identical overall correlation but opposite tails."""

    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, n)
    y = rng.normal(0.0, 1.2, n)

    lower = x <= np.quantile(x, 0.35)
    y[lower] = x[lower] + rng.normal(0.0, 0.03, int(np.count_nonzero(lower)))
    upper = x >= np.quantile(x, 0.65)
    y[upper] = np.mean(y) + rng.normal(0.0, 0.05, int(np.count_nonzero(upper)))

    # Mirroring both variables preserves ordinary Pearson/Spearman correlation
    # while moving the strong dependence from the lower to the upper tail.
    left_tail_pair = (x, y)
    right_tail_pair = (-x, -y)
    return left_tail_pair, right_tail_pair


def demo_cube_call(ds: xr.Dataset) -> plt.Figure:
    """Show how the same plotting layer is called from a synchrony cube.

    Expected structure: ``ds["severity_synchrony"]`` has dimensions
    ``("time", "y", "x")`` or equivalent coordinates that select one series
    per location.
    """

    return plot_tail_association_from_cube(
        ds,
        var="severity_synchrony",
        selector_a={"isel": {"y": 0, "x": 0}},
        selector_b={"isel": {"y": 2, "x": 3}},
        preprocess="zscore",
        labels=("Pixel A", "Pixel B"),
        title_prefix="Tail association from extracted climate synchrony series",
    )


def main(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    left_pair, right_pair = synthetic_tail_pairs()
    outpath = output_dir / "ghosh_tail_association_climate_sync_demo"

    fig = plot_tail_association_grid(
        [left_pair, right_pair],
        b=1.0 / 3.0,
        labels=("Location A", "Location B"),
        row_titles=("Left-tail dominant", "Right-tail dominant"),
        outpath=outpath,
        title="Copula-style tail association plots for climate synchrony",
        subtitle="Mirrored synthetic series have the same ordinary correlation but opposite tail structure.",
    )
    plt.close(fig)

    for row_name, pair in zip(("left", "right"), (left_pair, right_pair)):
        stats, *_ = tail_association_stats(*pair)
        print(
            f"{row_name}: Pearson={stats.pearson:.3f}, Spearman={stats.spearman:.3f}, "
            f"lower={stats.lower_partial_spearman:.3f}, upper={stats.upper_partial_spearman:.3f}, "
            f"dominance={stats.dominance}"
        )
    print("wrote:", outpath.with_suffix(".png"))
    print("wrote:", outpath.with_suffix(".pdf"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/assets/figures"),
        help="Directory for PNG and PDF outputs.",
    )
    args = parser.parse_args()
    main(args.output_dir)
