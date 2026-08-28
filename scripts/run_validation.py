#!/usr/bin/env python3
"""Run publication QA against real PRISM data and the rendered cube viewer.

Each module writes a machine-readable result and a visual diagnostic. Expected-
failure controls prove that the suite rejects known data and rendering defects.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import colormaps, colors
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from PIL import Image
import xarray as xr

from cubedynamics import pipe, verbs as v
from cubedynamics.plotting.cube_viewer import cube_from_dataarray


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "real_data" / "prism_boulder_january_2024.nc"
PROVENANCE = FIXTURE.with_suffix(".provenance.json")
VIGNETTES = ROOT / "docs" / "vignettes"
VIGNETTE_INPUTS = {
    "tests/fixtures/real_data/prism_boulder_january_2024.nc":
        "tests/fixtures/real_data/prism_boulder_january_2024.provenance.json",
    "tests/fixtures/real_data/usgs_streamflow":
        "tests/fixtures/real_data/usgs_streamflow/provenance.json",
    "tests/fixtures/real_data/source_lessons/elevation.nc":
        "tests/fixtures/real_data/source_lessons/elevation.provenance.json",
    "tests/fixtures/real_data/source_lessons/roads_overture.geojson":
        "tests/fixtures/real_data/source_lessons/roads.provenance.json",
}
DEFAULT_OUTPUT = ROOT / "artifacts" / "validation"
FACE_PATTERN = re.compile(
    r'class="cd-face cd-(front|back|left|right|top|bottom)"[^>]*'
    r"url\('data:image/png;base64,([^']+)'\)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_result(output: Path, name: str, checks: dict, figure) -> dict:
    module_dir = output / name
    module_dir.mkdir(parents=True, exist_ok=True)
    passed = all(bool(value) for value in checks.values())
    payload = {"module": name, "status": "PASS" if passed else "FAIL", "checks": checks}
    (module_dir / "result.json").write_text(json.dumps(payload, indent=2) + "\n")
    figure.savefig(module_dir / "diagnostic.png", dpi=170, bbox_inches="tight")
    plt.close(figure)
    require(passed, f"{name} validation failed")
    return payload


def load_real_fixture() -> tuple[xr.Dataset, dict]:
    require(FIXTURE.exists(), f"missing fixture: {FIXTURE}")
    require(PROVENANCE.exists(), f"missing provenance: {PROVENANCE}")
    return xr.open_dataset(FIXTURE, engine="scipy").load(), json.loads(PROVENANCE.read_text())


def validate_data(output: Path, dataset: xr.Dataset, provenance: dict) -> dict:
    expected_time = np.arange(
        np.datetime64("2024-01-01"), np.datetime64("2024-01-31"), np.timedelta64(1, "D")
    )
    checks = {
        "fixture_sha256_matches": sha256(FIXTURE) == provenance["fixture_sha256"],
        "official_source_declared": dataset.attrs.get("source") == "PRISM Group, Oregon State University",
        "observational_not_generated": dataset.attrs.get("is_synthetic") == 0
        and provenance.get("is_synthetic") is False,
        "dimensions_exact": dict(dataset.sizes) == {"time": 30, "y": 24, "x": 24},
        "daily_time_complete": np.array_equal(dataset.time.values.astype("datetime64[D]"), expected_time),
        "coordinates_ordered": bool(np.all(np.diff(dataset.x) > 0) and np.all(np.diff(dataset.y) < 0)),
        "all_cells_finite": all(bool(np.isfinite(dataset[name]).all()) for name in dataset.data_vars),
        "physical_order_tmin_lte_tmax": bool((dataset.tmin <= dataset.tmax).all()),
        "derived_range_exact": bool(
            np.allclose(dataset.diurnal_range, dataset.tmax - dataset.tmin, rtol=0, atol=1e-5)
        ),
        "source_archive_evidence_complete": len(provenance.get("source_archives", [])) == 60
        and all(record.get("sha256") and record.get("url") for record in provenance["source_archives"]),
    }

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.7), constrained_layout=True)
    dataset.tmin.mean("time").plot(ax=axes[0], cmap="coolwarm", cbar_kwargs={"label": "°C"})
    axes[0].set_title("Observed PRISM mean minimum")
    dataset.tmax.mean("time").plot(ax=axes[1], cmap="magma", cbar_kwargs={"label": "°C"})
    axes[1].set_title("Observed PRISM mean maximum")
    dataset[["tmin", "tmax"]].mean(("y", "x")).to_dataframe().plot(ax=axes[2])
    axes[2].set_title("Regional daily observations")
    axes[2].set_ylabel("Temperature (°C)")
    return write_result(output, "data", checks, fig)


def validate_grammar(output: Path, dataset: xr.Dataset) -> dict:
    cube = dataset.tmax
    direct_z = (cube - cube.mean("time")) / cube.std("time")
    piped_z = (pipe(cube) | v.zscore(dim="time")).unwrap()
    direct_method = (cube - cube.mean("time")).mean(("y", "x"))
    piped_method = (
        pipe(cube) | v.anomaly(dim="time") | v.mean(dim=("y", "x"), keep_dim=False)
    ).unwrap()
    z_error = float(abs(direct_z - piped_z).max())
    method_error = float(abs(direct_method - piped_method).max())
    checks = {
        "zscore_matches_xarray": z_error < 1e-6,
        "composed_pipe_matches_direct": method_error < 1e-6,
        "coordinates_preserved": all(np.array_equal(piped_z[name], cube[name]) for name in cube.dims),
        "source_provenance_preserved": piped_z.attrs.get("source") == cube.attrs.get("source"),
    }

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), constrained_layout=True)
    piped_method.plot(ax=axes[0], marker="o", color="#2f6f6d")
    axes[0].axhline(0, color="0.4", linewidth=0.8)
    axes[0].set_title("Pipe result on observed PRISM data")
    axes[0].set_ylabel("Regional anomaly (°C)")
    axes[1].bar(["z-score", "composed method"], [z_error, method_error], color="#b56b45")
    axes[1].set_yscale("symlog", linthresh=1e-16)
    axes[1].set_title("Maximum absolute pipe/direct error")
    return write_result(output, "grammar", checks, fig)


def expected_face_values(values: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "front": values[-1],
        "back": np.flip(values[0], axis=1),
        "left": values[:, :, 0].T,
        "right": values[::-1, :, -1].T,
        "top": values[:, -1, :],
        "bottom": values[::-1, 0, :],
    }


def decode_faces(html: str) -> dict[str, np.ndarray]:
    matches = FACE_PATTERN.findall(html)
    require(len(matches) == 6, f"expected exactly six cube faces, found {len(matches)}")
    require(len({name for name, _ in matches}) == 6, "cube face names must be unique")
    return {
        name: np.asarray(Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA"))
        for name, payload in matches
    }


def expected_rgba(values: np.ndarray, cmap: str, limits: tuple[float, float]) -> np.ndarray:
    norm = colors.Normalize(vmin=limits[0], vmax=limits[1])
    return (colormaps.get_cmap(cmap)(norm(values.astype("float32"))) * 255).astype("uint8")


def build_real_cube_evidence(dataset: xr.Dataset):
    sample = dataset.tmax.isel(time=slice(0, 8), y=slice(7, 14), x=slice(8, 16))
    values = np.asarray(sample.values)
    limits = (float(values.min()), float(values.max()))
    html = cube_from_dataarray(
        sample,
        cmap="magma",
        fill_limits=limits,
        thin_time_factor=1,
        show_progress=False,
        return_html=True,
    )
    return sample, values, limits, html, decode_faces(html)


def validate_cube(output: Path, dataset: xr.Dataset) -> dict:
    sample, values, limits, html, actual = build_real_cube_evidence(dataset)
    expected_values = expected_face_values(values)
    exact = {
        face: np.array_equal(actual[face], expected_rgba(reference, "magma", limits))
        for face, reference in expected_values.items()
    }
    checks = {
        "six_unique_shell_faces": len(actual) == 6,
        "complete_textures_not_css_cropped": "background-size: 100% 100%" in html
        and "background-size: cover" not in html,
        "front_is_newest": exact["front"],
        "back_is_oldest_with_declared_x_reversal": exact["back"],
        "left_time_oldest_to_newest": exact["left"],
        "right_time_newest_to_oldest": exact["right"],
        "top_time_oldest_to_newest": exact["top"],
        "bottom_time_newest_to_oldest": exact["bottom"],
        "every_rgba_pixel_exact": all(exact.values()),
    }

    fig, axes = plt.subplots(2, 3, figsize=(11, 6.8), constrained_layout=True)
    for ax, face in zip(axes.flat, ("front", "back", "left", "right", "top", "bottom")):
        ax.imshow(actual[face], interpolation="nearest")
        ax.set_title(f"{face} · exact={exact[face]}")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle(
        f"Decoded HTML textures · real PRISM tmax · {sample.sizes['time']} dates",
        fontweight="bold",
    )
    return write_result(output, "cube", checks, fig)


def vignette_input_verified(metadata: dict) -> bool:
    """Verify an explicitly supported input, not an arbitrary provenance claim.

    This validates retained input integrity, not production-source certification.
    New providers require an intentional fixture/contract addition here.
    """
    fixture_name = metadata.get("data_fixture")
    provenance_name = VIGNETTE_INPUTS.get(fixture_name)
    if not provenance_name or metadata.get("provenance") != provenance_name:
        return False
    try:
        fixture = ROOT / fixture_name
        provenance = json.loads((ROOT / provenance_name).read_text())
        if "files" in provenance and fixture.suffix in {".nc", ".geojson"}:
            base = fixture.parent
            return provenance.get("is_synthetic") is False and fixture.name in provenance["files"] and all(
                not Path(relative).is_absolute()
                and (base / relative).resolve().is_relative_to(base.resolve())
                and sha256(base / relative) == digest
                for relative, digest in provenance["files"].items()
            )
        if fixture.is_file():
            return provenance.get("is_synthetic") is False and sha256(fixture) == provenance["fixture_sha256"]
        files = provenance["files"]
        actual = {str(p.relative_to(fixture)) for p in fixture.rglob("*") if p.is_file()
                  and p != ROOT / provenance_name}
        return bool(files) and set(files) == actual and all(
            not Path(relative).is_absolute()
            and (fixture / relative).resolve().is_relative_to(fixture.resolve())
            and sha256(fixture / relative) == digest
            for relative, digest in files.items()
        )
    except (OSError, KeyError, TypeError, ValueError):
        return False


def validate_vignettes(output: Path, run_notebooks: bool) -> dict:
    paths = sorted(VIGNETTES.glob("*.ipynb"))
    required_lessons = {"cube_from_arrays", "cube_from_dataset", "cube_from_tidy_table",
                        "grammar_basics", "verbs_gallery", "states_and_events",
                        "custom_verb_project", "lazy_composition", "streamflow_snapshots",
                        "elevation_landscape", "roads_local_network"}
    checks = {
        "required_lessons_present": required_lessons <= {path.stem for path in paths},
        "all_marked_supported": True,
        "all_use_real_fixture": True,
        "all_record_provenance": True,
        "all_fixture_checksums_match": True,
        "all_are_offline": True,
        "all_emit_static_plot_code": True,
        "no_random_data_generation": True,
        "public_learning_paths_use_observations": True,
        "historical_generated_assets_not_published": True,
        "homepage_cube_uses_reviewed_prism": True,
    }
    plot_cells = []
    for path in paths:
        notebook = json.loads(path.read_text())
        metadata = notebook.get("metadata", {}).get("cubedynamics", {})
        source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        checks["all_marked_supported"] &= metadata.get("supported_vignette") is True
        expected_provenance = VIGNETTE_INPUTS.get(metadata.get("data_fixture"))
        checks["all_use_real_fixture"] &= expected_provenance is not None
        checks["all_record_provenance"] &= expected_provenance is not None and metadata.get("provenance") == expected_provenance
        checks["all_fixture_checksums_match"] &= vignette_input_verified(metadata)
        checks["all_are_offline"] &= metadata.get("network") is False
        checks["all_emit_static_plot_code"] &= "plt.show()" in source
        checks["no_random_data_generation"] &= "np.random" not in source and "default_rng" not in source
        plot_cells.append(sum("plt.show()" in "".join(cell.get("source", [])) for cell in notebook["cells"]))

    learning_pages = [
        ROOT / "docs" / "index.md",
        VIGNETTES / "index.md",
        ROOT / "docs" / "synchrony" / "index.md",
        ROOT / "docs" / "synchrony" / "biology_coupling.md",
        ROOT / "docs" / "synchrony" / "primitives.md",
        ROOT / "docs" / "synchrony" / "state_events.md",
        ROOT / "docs" / "synchrony" / "center_recipe.md",
        ROOT / "docs" / "capabilities" / "fire-vase.md",
        ROOT / "docs" / "workflows" / "fire_analysis.md",
        ROOT / "docs" / "recipes" / "index.md",
        ROOT / "docs" / "viz" / "index.md",
    ]
    forbidden_public_examples = (
        "synthetic example",
        "synthetic cube",
        "synthetic fire",
        "fire_vase_synthetic",
        "fireeventdaily.example()",
        "fire_vase_panel_sample",
        "synchrony_occurrence_cube",
        "synchrony_coupling_lag_curve",
        "synchrony_severity_cube",
        "synchrony_event_timing_duration_panel",
        "climate_median_split_synchrony_cube",
        "synchrony_event_diagnostics",
    )
    checks["public_learning_paths_use_observations"] = all(
        not any(phrase in page.read_text(encoding="utf-8").lower() for phrase in forbidden_public_examples)
        for page in learning_pages
    )
    site_config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    historical_generated_assets = (
        "recipes/fire_vase_synthetic.md",
        "recipes/climate_tail_dep_center.md",
        "recipes/ghosh_tail_association.md",
        "assets/figures/fire_vase_panel_sample.html",
        "assets/figures/synchrony_occurrence_cube.html",
        "assets/figures/synchrony_metric_comparison.png",
        "assets/figures/synchrony_coupling_lag_curve.png",
        "assets/figures/synchrony_severity_cube.html",
        "assets/figures/synchrony_event_timing_duration_panel.html",
        "assets/figures/climate_median_split_synchrony_cube.html",
        "assets/figures/synchrony_event_diagnostics.png",
    )
    checks["historical_generated_assets_not_published"] = all(
        path in site_config for path in historical_generated_assets
    )
    homepage_cube = ROOT / "docs" / "assets" / "figures" / "prism_boulder_tmax_cube.html"
    homepage_html = homepage_cube.read_text(encoding="utf-8") if homepage_cube.exists() else ""
    checks["homepage_cube_uses_reviewed_prism"] = (
        "Observed PRISM daily maximum temperature" in homepage_html
        and len(FACE_PATTERN.findall(homepage_html)) == 6
        and "background-size: cover" not in homepage_html
    )

    if run_notebooks:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "run_vignettes.py")],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        checks["all_notebooks_execute"] = completed.returncode == 0
        (output / "notebook-execution.log").write_text(completed.stdout + completed.stderr)
        print(completed.stdout, end="")
        if completed.returncode:
            print(completed.stderr, file=sys.stderr)

    fig, ax = plt.subplots(figsize=(10, 4.2), constrained_layout=True)
    ax.bar([path.stem.replace("_", "\n") for path in paths], plot_cells, color="#547b75")
    ax.set_title("Static plot outputs required by every real-data vignette")
    ax.set_ylabel("Plot-emitting cells")
    ax.tick_params(axis="x", labelsize=8)
    return write_result(output, "vignettes", checks, fig)


def validate_contrasts(output: Path, dataset: xr.Dataset) -> dict:
    _, values, limits, html, actual = build_real_cube_evidence(dataset)
    expected = expected_face_values(values)

    def face_matches(face: str, candidate: np.ndarray) -> bool:
        return np.array_equal(actual[face], expected_rgba(candidate, "magma", limits))

    duplicate_html = html.replace(
        '<div class="cd-face cd-back"',
        '<div class="cd-face cd-front" style="background-image: url(\'data:image/png;base64,AAAA\');"></div>'
        '<div class="cd-face cd-back"',
        1,
    )
    try:
        decode_faces(duplicate_html)
        duplicate_rejected = False
    except (AssertionError, ValueError):
        duplicate_rejected = True

    cropped_html = html.replace("background-size: 100% 100%", "background-size: cover", 1)
    cropped_rejected = not (
        "background-size: 100% 100%" in cropped_html
        and "background-size: cover" not in cropped_html
    )

    controls = {
        "unreversed_back": not face_matches("back", values[0]),
        "unreversed_right_time": not face_matches("right", values[:, :, -1].T),
        "transposed_top_time_axis": not face_matches("top", values[:, -1, :].T),
        "unreversed_bottom_time": not face_matches("bottom", values[:, 0, :]),
        "duplicate_front_face": duplicate_rejected,
        "cropping_css": cropped_rejected,
    }
    checks = {f"rejects_{name}": value for name, value in controls.items()}

    fig, ax = plt.subplots(figsize=(10, 4.2), constrained_layout=True)
    ax.barh(list(checks), [int(value) for value in checks.values()], color="#9b5943")
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("Rejected as expected (1 = yes)")
    ax.set_title("Expected-failure controls")
    return write_result(output, "contrast", checks, fig)


def collate_pdf(output: Path, results: list[dict]) -> None:
    with PdfPages(output / "validation_report.pdf") as pdf:
        for result in results:
            image = plt.imread(output / result["module"] / "diagnostic.png")
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.imshow(image)
            ax.axis("off")
            fig.suptitle(f"CubeDynamics validation · {result['module']} · {result['status']}")
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--run-vignettes", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    dataset, provenance = load_real_fixture()
    results = [
        validate_data(args.output, dataset, provenance),
        validate_grammar(args.output, dataset),
        validate_cube(args.output, dataset),
        validate_vignettes(args.output, args.run_vignettes),
        validate_contrasts(args.output, dataset),
    ]
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "fixture_sha256": provenance["fixture_sha256"],
        "status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL",
        "modules": results,
    }
    (args.output / "suite_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    collate_pdf(args.output, results)
    print(f"{manifest['status']} · {len(results)} validation modules")
    print(f"evidence: {args.output}")
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
