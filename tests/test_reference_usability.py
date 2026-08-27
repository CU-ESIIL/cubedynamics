"""Semantic browsing and navigation contracts, without live data requests."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_reference_docs as reference
from reference_classification import CATEGORIES, COMPATIBILITY, PLACEHOLDERS, classify


def routes(items):
    if isinstance(items, str):
        return {items}
    if isinstance(items, dict):
        return set().union(*(routes(v) for v in items.values()))
    return set().union(*(routes(v) for v in items)) if items else set()


def nav_config():
    pytest.importorskip("mkdocs")
    from mkdocs.config import load_config
    from docs_hooks import on_config
    return on_config(load_config(str(ROOT / "mkdocs.yml")))


def test_real_callables_are_categorized_and_full_az_is_reachable():
    pages = reference.generate()
    names = reference.public_verbs()
    assigned = [n for group in CATEGORIES.values() for n in group]
    assert len(set(assigned)) == len(assigned)
    assert set(assigned) | PLACEHOLDERS | COMPATIBILITY.keys() <= names.keys()
    for name, func in names.items():
        info = classify(name, func)
        target = f"]({name}.md)"
        assert target in pages["reference/verbs/a-z.md"]
        if info["status"] == "implemented":
            assert info["category"] in {*CATEGORIES, "Other helpers"}
            assert target in pages["reference/verbs/index.md"]
        else:
            assert target not in pages["reference/verbs/index.md"]
            if info["status"] in {"compatibility", "deprecated"}:
                assert target in pages["reference/verbs/compatibility.md"]


@pytest.mark.parametrize("name", sorted(PLACEHOLDERS))
def test_placeholders_are_explicit_and_not_promoted(name):
    pages = reference.generate()
    assert classify(name, reference.public_verbs()[name])["status"] == "placeholder"
    assert f"]({name}.md)" in pages["reference/verbs/planned.md"]
    assert "Not implemented" in pages[f"reference/verbs/{name}.md"]
    assert "Reserved / planned API" in pages[f"reference/verbs/{name}.md"]


@pytest.mark.parametrize("name", sorted(COMPATIBILITY))
def test_compatibility_is_distinct_from_implemented_and_reserved(name):
    pages = reference.generate()
    assert classify(name, reference.public_verbs()[name])["status"] in {"compatibility", "deprecated"}
    assert f"]({name}.md)" in pages["reference/verbs/compatibility.md"]
    assert "Compatibility / legacy" in pages[f"reference/verbs/{name}.md"] or "**Deprecated:**" in pages[f"reference/verbs/{name}.md"]


def test_month_filter_is_a_supported_stage():
    info = classify("month_filter", reference.v.month_filter)
    assert info["status"] == "implemented"
    assert info["kind"] == "stage"
    assert reference.v.month_filter.__module__ == "cubedynamics.verbs.stats"


def test_newly_deprecated_callable_needs_no_second_inventory_entry(monkeypatch):
    def classify_with_deprecation(name, func):
        info = classify(name, func)
        if name == "mean":
            info["status"] = "deprecated"
        return info

    monkeypatch.setattr(reference, "classify", classify_with_deprecation)
    pages = reference.generate()
    assert "](mean.md)" not in pages["reference/verbs/index.md"]
    assert "](mean.md)" in pages["reference/verbs/compatibility.md"]
    assert "**Deprecated:**" in pages["reference/verbs/mean.md"]


@pytest.mark.parametrize(("name", "kind"), [
    ("plot", "stage"), ("diagnostic_panel", "stage"), ("exceedance", "stage"),
    ("mean", "stage"), ("landsat8_mpc", "stage"),
    ("rasterize_observations", "helper"), ("vase_mask", "helper"),
    ("fire_plot", "visualization_helper"), ("fire_derivative", "visualization_helper"),
])
def test_calling_conventions_follow_implementation_not_registry_membership(name, kind):
    assert classify(name, reference.public_verbs()[name])["kind"] == kind


def test_multisource_nouns_compare_declared_source_facts():
    pages = reference.generate()
    for noun, sources in reference.data.list_sources().items():
        text = pages[f"library/nouns/{noun}.md"]
        if len(sources) < 2:
            continue
        differences = text.split("## Differences among source flavors", 1)[1].split("\n## ", 1)[0]
        for source in sources:
            info = reference.data.describe(noun, source)
            for key in ("units", "source_variables", "spatial_resolution", "temporal_resolution", "coverage", "update_cadence", "limitations"):
                assert reference.cell(info[key]) in differences
        assert "not silently harmonize" in differences


def test_user_navigation_separates_developer_material_and_keeps_all_references():
    config = nav_config()
    docs = next(g["Documents"] for g in config["nav"] if "Documents" in g)
    developer = next(g["Developer documentation"] for g in docs if "Developer documentation" in g)
    user = [g for g in docs if "Developer documentation" not in g]
    assert "developer/index.md" in routes(developer)
    assert not any(path.startswith(("dev/", "developer/", "design/")) for path in routes(user))
    for path in ("project/publication_plan.md", "project/deprecation_inventory.md", "project/grammar_inventory.md", "api/inventory_full.md", "dev/cube_viewer_invariants.md"):
        assert path in routes(developer) and path not in routes(user)
    for name in reference.public_verbs():
        assert f"reference/verbs/{name}.md" in routes(docs)
    landing = (ROOT / "docs/documentation/index.md").read_text()
    assert "../developer/index.md" in landing
    assert not any(path in landing for path in ("publication_plan.md", "deprecation_inventory.md", "ci_testing.md"))


def test_library_navigation_follows_generated_categories_without_manual_noun_list(tmp_path):
    pytest.importorskip("mkdocs")
    from docs_hooks import on_config
    (tmp_path / "library").mkdir()
    (tmp_path / "library/index.md").write_text("# Library\n## New category\n| [new_noun](nouns/new_noun.md) | Description |\n")
    config = {"docs_dir": tmp_path, "nav": [{"Library": [{"All nouns": "library/index.md"}]}]}
    result = on_config(config)["nav"][0]["Library"]
    assert {"New category": [{"new_noun": "library/nouns/new_noun.md"}]} in result


def test_noun_verb_and_vignette_crosslinks_survive():
    pages = reference.generate()
    assert "vignettes/grammar_basics.ipynb" in pages["library/nouns/temperature.md"]
    assert "reference/verbs/mean.md" in pages["library/nouns/temperature.md"]
    assert "learn/verbs.md" in pages["reference/verbs/mean.md"]
    assert "vignettes/grammar_basics.ipynb" in pages["reference/verbs/mean.md"]
