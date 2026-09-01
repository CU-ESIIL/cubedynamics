#!/usr/bin/env python3
"""Inspect distributions and test an exact installed wheel, without editable code.

Use --inspect-only in the build environment. Otherwise run this script with
the external wheel environment's Python -I. Only --repo-example reads fixture
data; the package-only smoke has no repository data dependency.
"""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "cubedynamics/__init__.py", "cubedynamics/piping.py", "cubedynamics/verbs/__init__.py",
    "cubedynamics/data/serving_history.json",
    "cubedynamics/viewers/templates/cube_viewer_template.html",
    "climate_cube_math/__init__.py", "climate_cube_math/demo.py", "climate_cube_math/hulls.py",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact_info(path):
    path = Path(path)
    return {"filename": path.name, "sha256": digest(path), "bytes": path.stat().st_size}


def check_members(names):
    """Reject repository-only payloads in either normalized archive inventory."""
    forbidden = {"tests", "test", "fixtures", "artifacts", "paper", "manuscripts", "notebooks",
                 "output", "outputs", "figures", "source_projects", "__pycache__", ".github", ".git"}
    for name in names:
        parts = PurePosixPath(name).parts
        require(not PurePosixPath(name).is_absolute() and ".." not in parts, f"Unsafe archive path: {name}")
        require(not forbidden.intersection(parts), f"Repository-only content packaged: {name}")
        require(not name.endswith((".ipynb", ".nc", ".tif", ".pdf", ".pyc")), f"Unexpected package data: {name}")


def inspect_distributions(wheel, sdist=None):
    with zipfile.ZipFile(wheel) as archive:
        names = {n for n in archive.namelist() if not n.endswith("/")}
        check_members(names)
        require(REQUIRED <= names, f"Missing wheel assets: {sorted(REQUIRED - names)}")
        meta_names = [n for n in names if n.endswith(".dist-info/METADATA")]
        require(len(meta_names) == 1, "Expected one wheel METADATA record")
        info = BytesParser().parsebytes(archive.read(meta_names[0]))
        require(info["Name"] == "cubedynamics" and info["Version"] == "0.1.0rc1", "Unexpected release name/version")
        package_files = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in names
                         if n.startswith(("cubedynamics/", "climate_cube_math/"))}
    result = {"wheel": artifact_info(wheel), "version": info["Version"], "wheel_members": sorted(names),
              "requires_dist": info.get_all("Requires-Dist", []), "status": "PASS"}
    if sdist:
        with tarfile.open(sdist) as archive:
            files = [m for m in archive.getmembers() if m.isfile()]
            roots = {PurePosixPath(m.name).parts[0] for m in files}
            require(len(roots) == 1, "sdist must have one root")
            members = {str(PurePosixPath(m.name).relative_to(next(iter(roots)))): m for m in files}
            check_members(members)
            require({"pyproject.toml", "README.md", "LICENSE", "CITATION.cff"} <= members.keys(), "Missing sdist metadata")
            for name, expected in package_files.items():
                member = members.get("src/" + name)
                require(member is not None, f"sdist lacks wheel runtime file: {name}")
                require(hashlib.sha256(archive.extractfile(member).read()).hexdigest() == expected,
                        f"Wheel/sdist runtime mismatch: {name}")
            source_meta = BytesParser().parsebytes(archive.extractfile(members["PKG-INFO"]).read())
            require(source_meta["Version"] == info["Version"], "sdist version differs")
        result.update(sdist=artifact_info(sdist), sdist_members=sorted(members))
    return result


def archive_sha256(info):
    """Read modern/legacy direct_url hashes without accepting absent evidence."""
    require(isinstance(info, dict), "Invalid archive origin metadata")
    hashes = info.get("hashes", {})
    require(isinstance(hashes, dict), "Invalid archive hashes metadata")
    if "hash" in info:
        legacy = info["hash"]
        require(isinstance(legacy, str), "Invalid legacy archive hash")
        algorithm, separator, value = legacy.partition("=")
        require(algorithm and separator and value, "Invalid legacy archive hash")
        if "hashes" in info:
            require(hashes.get(algorithm) == value, "Conflicting archive hash metadata")
        else:
            hashes = {algorithm: value}
    value = hashes.get("sha256")
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value),
            "Wheel origin metadata lacks a valid SHA256; upgrade pip in the wheel "
            "environment and reinstall the supplied wheel")
    return value.lower()


def check_installed_wheel(wheel, repo=ROOT):
    """Reject editable/wrong artifacts and verify loaded code plus package data."""
    import cubedynamics
    import cubedynamics.verbs
    repo = Path(repo).resolve()
    wheel = Path(wheel).resolve()
    dist = metadata.distribution("cubedynamics")
    installed = Path(dist.locate_file("")).resolve()
    require(not installed.is_relative_to(repo), "Release environment must be outside the checkout")
    require(sys.prefix != sys.base_prefix, "Use a fresh virtual environment for the wheel check")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    require(not direct.get("dir_info", {}).get("editable", False), "Editable installation is not a wheel test")
    expected = archive_sha256(direct.get("archive_info", {}))
    require(expected == digest(wheel), "Installed distribution is not the supplied wheel (SHA256 differs)")
    with zipfile.ZipFile(wheel) as archive:
        files = {n for n in archive.namelist() if n.startswith(("cubedynamics/", "climate_cube_math/")) and not n.endswith("/")}
        require(REQUIRED <= files, "Wheel lacks required runtime assets")
        for name in files:
            actual = Path(dist.locate_file(name)).resolve()
            require(actual.is_relative_to(installed) and not actual.is_relative_to(repo), f"Checkout import: {actual}")
            require(actual.is_file() and actual.read_bytes() == archive.read(name), f"Installed wheel file changed: {name}")
        for name, module in list(sys.modules.items()):
            if name.split(".")[0] not in {"cubedynamics", "climate_cube_math"}:
                continue
            location = getattr(module, "__file__", None)
            if location:
                path = Path(location).resolve()
                require(path.is_relative_to(installed) and not path.is_relative_to(repo), f"Source checkout leaked into kernel: {path}")
                require(path.relative_to(installed).as_posix() in files, f"Unpackaged module loaded: {name}")
    require(cubedynamics.__version__ == dist.version == "0.1.0rc1", "Runtime/installed metadata version mismatch")
    return {"version": dist.version, "module": str(Path(cubedynamics.__file__).resolve()),
            "python": sys.version.split()[0], "executable": sys.executable,
            "wheel": artifact_info(wheel), "checked_package_files": len(files)}


def verify_mean_semantics(cube, actual):
    """Verify numerical xarray parity plus CubeDynamics result semantics."""

    import xarray as xr

    expected = cube.mean("time", keep_attrs=True)
    xr.testing.assert_allclose(actual, expected)
    require(actual.coords.equals(expected.coords), "Reducer coordinates changed")
    require(actual.attrs.get("semantic_kind") == "summary", "Reducer semantic kind is stale")
    require(actual.attrs.get("summary_operation") == "mean", "Reducer summary operation missing")
    require(actual.attrs.get("units") == cube.attrs.get("units"), "Reducer lost physical units")


def smoke():
    import numpy as np
    import xarray as xr
    from cubedynamics import Pipe, data, pipe, verbs as v
    # Deliberate deterministic unit input, not a scientific example dataset.
    cube = xr.DataArray(np.arange(12.).reshape(3, 2, 2), dims=("time", "y", "x"),
                        coords={"time": np.arange(3), "y": [0, 1], "x": [0, 1]},
                        attrs={"units": "K", "source": "package-only unit control"})
    wrapped = pipe(cube)
    require(isinstance(wrapped, Pipe) and wrapped.unwrap() is cube, "unwrap changed identity")
    result = wrapped | v.mean(over="time", keep_dim=False)
    verify_mean_semantics(cube, result.unwrap())
    require(result.unwrap().dims == ("y", "x"), "Reducer dimensions changed")
    require(len(result.semantic_trace) == 1 and isinstance(result.explain(), str), "Missing semantic trace")
    require(isinstance(result.suggest(), tuple), "Unexpected suggest result")
    result.validate()
    require(result.semantic_state.dimensions == ("y", "x"), "Semantic state lost dimensions")
    with warnings.catch_warnings(record=True) as notices:
        warnings.simplefilter("always")
        import climate_cube_math as legacy
    require(legacy.pipe is pipe and legacy.__version__ == "0.1.0rc1", "Compatibility import differs")
    require(any(issubclass(n.category, DeprecationWarning) for n in notices), "Compatibility warning missing")
    catalog = data.list_sources()
    require(len(catalog) == 8, "Catalog noun count changed")
    require({s for variants in catalog.values() for s in variants} == {"prism", "gridmet", "sentinel2"}, "Candidate promoted into catalog")
    data.describe("temperature", "prism")
    from cubedynamics.data import three_dep, roads, usgs
    require(all(callable(f) for f in (three_dep.elevation, roads.roads, usgs.streamflow)), "Candidate import missing")
    return {"status": "PASS", "dimensions": list(result.unwrap().dims), "numerical_result": result.unwrap().values.tolist(),
            "attrs_preserved_and_relabelled": True, "semantic_kind": result.unwrap().attrs["semantic_kind"],
            "catalog": catalog, "candidate_imports": "usable, not promoted"}


def readme_example(repo, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import xarray as xr
    from PIL import Image
    fixture = repo / "tests/fixtures/real_data/prism_boulder_january_2024.nc"
    provenance = json.loads(fixture.with_suffix(".provenance.json").read_text())
    require(digest(fixture) == provenance["fixture_sha256"], "README fixture hash mismatch")
    text = (repo / "README.md").read_text()
    code = re.search(r"<!-- readme-example: offline -->\s*```python\n(.*?)```", text, re.S).group(1)
    # Execute the actual README block, replacing only its external data location.
    code = code.replace("tests/fixtures/real_data/prism_boulder_january_2024.nc", fixture.as_posix())
    namespace = {}
    original_show = plt.show
    try:
        plt.show = lambda: None
        exec(compile(code, "README.md/offline", "exec"), namespace)
        expected = namespace["cube"].mean("time", keep_attrs=True)
        actual = namespace["result"].unwrap()
        xr.testing.assert_allclose(actual, expected)
        require(actual.coords.equals(expected.coords), "README reducer coordinates changed")
        require(actual.attrs.get("semantic_kind") == "summary", "README result lacks summary semantics")
        require(actual.attrs.get("summary_operation") == "mean", "README result lacks mean metadata")
        output.mkdir(parents=True, exist_ok=True)
        figure = output / "readme-prism.png"
        plt.gcf().savefig(figure, dpi=130, bbox_inches="tight")
        with Image.open(figure) as image:
            require(min(image.size) > 100 and any(a != b for a, b in image.convert("RGB").getextrema()), "Empty README figure")
    finally:
        plt.show = original_show
        plt.close("all")
    return {"status": "PASS", "fixture_sha256": digest(fixture), "figure": artifact_info(figure),
            "dimensions": list(expected.dims), "code": "README.md marked offline block"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--sdist", type=Path)
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument("--repo-example", action="store_true")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect_distributions(args.wheel, args.sdist)
    if not args.inspect_only:
        result["installation"] = check_installed_wheel(args.wheel, args.repo)
        result["package_only"] = smoke()
        if args.repo_example:
            result["readme_example"] = readme_example(args.repo.resolve(), args.output.parent)
        check_installed_wheel(args.wheel, args.repo)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS release artifact: {args.output}")


if __name__ == "__main__":
    main()
