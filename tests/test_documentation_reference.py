"""Publication contracts: coverage, generated ownership and real-data examples."""
from pathlib import Path
import ast
import inspect
import json
import re
import sys

import matplotlib.pyplot as plt
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_reference_docs as reference
from docs_examples import EXAMPLES, FIXTURE_SETUP


def test_site_has_five_purpose_driven_primary_tabs():
    config = (ROOT / "mkdocs.yml").read_text()
    nav = config.split("nav:\n", 1)[1].split("\nrepo_url:", 1)[0]
    assert re.findall(r"^  - ([^:]+):", nav, re.MULTILINE) == ["Home", "Learn", "Library", "Documents", "Vignettes"]


def test_generated_references_are_current_and_owned():
    pages = reference.generate()
    for path, expected in pages.items():
        assert (ROOT / "docs" / path).read_text() == expected, path
    actual = {str(p.relative_to(ROOT / "docs")) for directory in ("library/nouns", "library/sources", "reference/verbs") for p in (ROOT / "docs" / directory).glob("*.md")}
    assert actual <= pages.keys()


def test_verb_notes_do_not_repeat_malformed_docstring_parameter_sections():
    page = reference.generate()["reference/verbs/mean.md"]
    notes = page.split("## Implementation notes", 1)[1]
    assert "Parameters" not in notes
    assert "Streaming VirtualCube inputs" in notes
    assert "[Implementation source]" in notes


def test_every_catalog_noun_source_and_public_verb_has_reference():
    pages = reference.generate()
    for noun, sources in reference.data.list_sources().items():
        assert f"](nouns/{noun}.md)" in pages["library/index.md"]
        text = pages[f"library/nouns/{noun}.md"]
        for heading in reference.NOUN_SECTIONS:
            assert f"## {heading}\n" in text
        for source in sources:
            assert f"]({source}.md)" in pages["library/sources/index.md"]
            info = reference.data.describe(noun, source)
            assert info["current_serving_revision"] in text
            assert info["qa_profile"] in text
            for heading in reference.SOURCE_SECTIONS:
                assert f"## {heading}\n" in pages[f"library/sources/{source}.md"]
    for name in reference.public_verbs():
        assert f"]({name}.md)" in pages["reference/verbs/a-z.md"]
        for heading in reference.VERB_SECTIONS:
            assert f"## {heading}\n" in pages[f"reference/verbs/{name}.md"]


def test_homepage_cube_is_deferred_but_accessible():
    text = (ROOT / "docs/index.md").read_text()
    assert 'data-src="assets/figures/prism_boulder_tmax_cube.html"' in text
    assert 'loading="lazy"' in text
    assert "Open the interactive cube viewer" in text
    for route in ("learn/", "library/", "documentation/", "vignettes/"):
        assert f'href="{route}"' in text


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_reference_examples_execute_on_observed_fixture(name, monkeypatch):
    monkeypatch.chdir(ROOT)
    namespace = {}
    try:
        exec(compile(FIXTURE_SETUP + "\n" + EXAMPLES[name], f"reference/{name}", "exec"), namespace)
    finally:
        plt.close("all")


@pytest.mark.parametrize("page", sorted((ROOT / "docs/learn").glob("*.md")))
def test_learn_pages_are_progressive_and_examples_execute(page, monkeypatch):
    if page.name == "index.md":
        return
    text = page.read_text()
    for heading in ("Concept", "Tiny example", "Explanation", "Try it / worked example", "What to learn next"):
        assert f"## {heading}\n" in text
    setup = re.findall(r"```python\n(.*?)```", (page.parent / "index.md").read_text(), re.S)[0]
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    monkeypatch.chdir(ROOT)
    try:
        exec(compile(setup + "\n" + "\n".join(blocks), str(page), "exec"), {})
    finally:
        plt.close("all")


def test_vignettes_have_complete_shell_and_valid_section_equivalents():
    for path in (ROOT / "docs").glob("**/*.ipynb"):
        nb = json.loads(path.read_text())
        meta = nb.get("metadata", {}).get("cubedynamics", {})
        if not meta.get("supported_vignette"):
            continue
        text = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
        mapping = meta["documentation_sections"]
        assert set(mapping) == {"Question", "Grammar / pipeline", "Plain-language interpretation", "Analysis", "Result", "Data used", "Reproduce", "See also"}
        for heading in mapping.values():
            assert re.search(rf"^#{{2,3}} {re.escape(heading)}", text, re.M), (path, heading)


def test_reference_does_not_present_candidates_or_placeholders_as_implemented():
    pages = reference.generate()
    assert "library/nouns/roads.md" not in pages
    assert "library/sources/daymet.md" not in pages
    for name in ("correlation_cube", "fit_model"):
        assert "Not implemented" in pages[f"reference/verbs/{name}.md"]


@pytest.mark.parametrize("route", [
    "recipes/gridmet_variance_cube.md", "recipes/prism_variance_cube.md",
    "recipes/s2_ndvi_zcube.md", "examples/climate_ndvi_correlation.md",
    "recipes/recipe_template.md",
])
def test_maintained_recipe_shells_and_public_call_signatures(route):
    text = (ROOT / "docs" / route).read_text()
    for heading in ("Question", "Grammar / pipeline", "Plain-language interpretation",
                    "Analysis", "Result", "Data used", "Reproduce", "See also"):
        assert f"## {heading}\n" in text
    # Check documented API calls without fetching live data or inventing a fixture.
    for block in re.findall(r"```python\n(.*?)```", text, re.S):
        tree = ast.parse(block)
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                continue
            if not isinstance(call.func.value, ast.Name):
                continue
            module = {"data": reference.data, "v": reference.v}.get(call.func.value.id)
            if module is None:
                continue
            func = getattr(module, call.func.attr)
            inspect.signature(func).bind(
                *[None for _ in call.args],
                **{keyword.arg: None for keyword in call.keywords if keyword.arg},
            )
