#!/usr/bin/env python3
"""Execute the public quickstart with an installed wheel outside the checkout.

Downloads only the existing checksum-pinned public example. --live additionally
checks the separately documented provider request; it does not certify a source.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    checks = runpy.run_path(str(ROOT / "scripts/check_release_artifact.py"))
    installation = checks["check_installed_wheel"](args.wheel, ROOT)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import xarray as xr
    blocks = dict(re.findall(r"<!-- external-quickstart: (\w+) -->\s*```python\n(.*?)```",
                             (ROOT / "docs/quickstart.md").read_text(), re.S))
    namespace = {}
    plots = []
    original_show = plt.show
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def show():
        figure = plt.gcf()
        if not figure.axes:
            raise RuntimeError("Quickstart did not plot")
        destination = args.output.parent / f"quickstart-{len(plots) + 1}.png"
        figure.savefig(destination, dpi=120, bbox_inches="tight")
        plots.append(checks["artifact_info"](destination))
        plt.close(figure)
    plt.show = show
    transcript = io.StringIO()
    try:
        with contextlib.redirect_stdout(transcript):
            for name in ("observations", "analysis", "discovery") + (("live",) if args.live else ()):
                exec(compile(blocks[name], f"quickstart/{name}", "exec"), namespace)
        cube = namespace["temperature"]
        assert cube.attrs["units"] == "degC" and cube.attrs["is_synthetic"] == 0
        expected = (cube - cube.mean("time")).mean(("y", "x"))
        xr.testing.assert_allclose(namespace["spatial_anomaly"], expected)
        assert np.isfinite(expected).all() and len(plots) == (2 if args.live else 1)
        checks["check_installed_wheel"](args.wheel, ROOT)
        result = {"status": "PASS", "installation": installation, "plots": plots,
                  "public_input_url": namespace["url"], "public_input_sha256": namespace["expected"],
                  "live_noun": "PASS; not source certification" if args.live else "NOT_RUN",
                  "source_checkout_required": False, "help_and_discovery": "PASS"}
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        args.output.with_suffix(".log").write_text(transcript.getvalue())
    finally:
        plt.show = original_show
        plt.close("all")
    print(f"PASS external quickstart: {args.output}")


if __name__ == "__main__":
    main()
