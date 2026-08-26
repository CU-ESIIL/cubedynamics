"""Publication guardrails for the primary documentation experience."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_site_has_five_purpose_driven_primary_tabs() -> None:
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    nav = config.split("nav:\n", 1)[1].split("\nrepo_url:", 1)[0]
    labels = re.findall(r"^  - ([^:]+):", nav, flags=re.MULTILINE)

    assert labels == ["Home", "Get Started", "Vignettes", "Library", "Documentation"]


def test_primary_hubs_exist_and_share_the_gallery_system() -> None:
    for page in (
        ROOT / "docs" / "quickstart.md",
        ROOT / "docs" / "vignettes" / "index.md",
        ROOT / "docs" / "library" / "index.md",
        ROOT / "docs" / "documentation" / "index.md",
    ):
        text = page.read_text(encoding="utf-8")
        assert 'class="cd-hub"' in text
        assert 'class="cd-hub-hero"' in text
        assert 'class="cd-gallery' in text


def test_homepage_cube_is_deferred_but_remains_accessible() -> None:
    homepage = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    loader = (ROOT / "docs" / "javascripts" / "deferred-embeds.js").read_text(
        encoding="utf-8"
    )

    assert 'data-src="assets/figures/prism_boulder_tmax_cube.html"' in homepage
    assert 'loading="lazy"' in homepage
    assert "requestIdleCallback" in loader
    assert "IntersectionObserver" in loader
    assert "Open the interactive cube viewer" in homepage


def test_library_teaches_both_custom_nouns_and_verbs() -> None:
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "extending/custom_nouns.md" in config
    assert "extending/custom_verbs.md" in config
    assert (ROOT / "docs" / "extending" / "custom_nouns.md").exists()
