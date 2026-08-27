"""Keep the two root guides aligned with the checkout, without live requests."""
import ast
import hashlib
import inspect
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import matplotlib.pyplot as plt
import numpy as np
import pytest
import xarray as xr

from cubedynamics import __version__, data, pipe

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def examples():
    return dict(re.findall(
        r"<!-- readme-example: (\w+) -->\s*```python\n(.*?)```",
        README.read_text(encoding="utf-8"), re.S,
    ))


def test_readme_version_and_extras_match_packaging():
    text = README.read_text(encoding="utf-8")
    metadata = (ROOT / "pyproject.toml").read_text()
    declared = re.search(r'^version = "([^"]+)"', metadata, re.M).group(1)
    assert declared == __version__
    assert f"version {declared}, alpha" in text
    assert "Development Status :: 3 - Alpha" in metadata
    extras_section = metadata.split("[project.optional-dependencies]", 1)[1].split("[project.urls]", 1)[0]
    extras = set(re.findall(r"^(\w+) = \[", extras_section, re.M))
    documented = set(re.findall(r"^\| `(\w+)` \|", text.split("## A short pipe", 1)[0], re.M))
    assert documented == extras


def test_readme_noun_source_table_matches_implemented_catalog():
    text = README.read_text(encoding="utf-8").split("<!-- readme-catalog: start -->", 1)[1].split("<!-- readme-catalog: end -->", 1)[0]
    rows = re.findall(r"^\| `(\w+)` \| (.*?) \|$", text, re.M)
    assert len(rows) == len(data.list_sources())
    assert {noun: tuple(re.findall(r"`(\w+)`", sources)) for noun, sources in rows} == data.list_sources()


def test_readme_supported_notebook_count():
    supported = []
    for directory in ("vignettes", "decision_vignettes"):
        for path in (ROOT / "docs" / directory).glob("*.ipynb"):
            meta = json.loads(path.read_text())["metadata"].get("cubedynamics", {})
            if meta.get("supported_vignette"):
                assert meta.get("network") is False
                supported.append(path)
    # Deliberate summary count: a new supported lesson should update the guide.
    assert len(supported) == 9
    assert "nine supported offline notebooks" in README.read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", ["README.md", "AGENTS.md"])
def test_repository_guide_local_links_and_explicit_paths_exist(filename):
    text = (ROOT / filename).read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        url = urlsplit(target)
        if not url.scheme and not url.netloc and url.path:
            assert (ROOT / unquote(url.path)).exists(), (filename, target)
    # Ignore described output/credential paths that are intentionally absent.
    for target in re.findall(r"`((?:src|docs|scripts|tests|paper|tools|examples|manifests)/[^`\s*]+)`", text):
        assert (ROOT / target).exists(), (filename, target)


def test_readme_offline_examples_execute_and_plot_real_observations(monkeypatch):
    blocks = examples()
    assert set(blocks) == {"offline", "discovery", "live", "custom"}
    monkeypatch.chdir(ROOT)
    fixture = ROOT / "tests/fixtures/real_data/prism_boulder_january_2024.nc"
    provenance = json.loads(fixture.with_suffix(".provenance.json").read_text())
    assert hashlib.sha256(fixture.read_bytes()).hexdigest() == provenance["fixture_sha256"]
    assert provenance["is_synthetic"] is False

    def no_network(*args, **kwargs):
        pytest.fail("Offline README examples attempted a network request")

    monkeypatch.setattr("requests.sessions.Session.request", no_network)
    shown = []
    monkeypatch.setattr(plt, "show", lambda: shown.append(bool(plt.gcf().axes)))
    namespace = {}
    try:
        for name in ("offline", "discovery", "custom"):
            exec(compile(blocks[name], f"README/{name}", "exec"), namespace)
        cube = namespace["cube"]
        assert cube.attrs["units"] == "degC"
        assert cube.attrs["is_synthetic"] == 0
        xr.testing.assert_allclose(namespace["result"].unwrap(), cube.mean("time"))
        expected = (cube > 10).mean("time").rename("fraction_above")
        xr.testing.assert_allclose(namespace["warm_days"], expected)
        assert shown == [True, True], "Each analytical example must display a plot"

        # A masked copy of real observations exercises the documented missingness rule.
        masked = cube.where(cube.x != cube.x[0])
        stage = namespace["fraction_above"](10)
        direct = stage(masked)
        xr.testing.assert_identical(direct, (pipe(masked) | stage).unwrap())
        assert np.isnan(direct.isel(x=0)).all()
        assert direct.attrs["units"] == "1"
    finally:
        plt.close("all")


def test_readme_live_request_matches_signature_and_catalog_without_fetching():
    tree = ast.parse(examples()["live"])
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute)
             and isinstance(node.func.value, ast.Name)
             and node.func.value.id == "data"]
    assert len(calls) == 1
    call = calls[0]
    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
    inspect.signature(getattr(data, call.func.attr)).bind(**kwargs)
    assert kwargs["source"] in data.sources(call.func.attr)
    facts = data.describe(call.func.attr, kwargs["source"])
    assert kwargs["statistic"] in facts["source_variables"]
