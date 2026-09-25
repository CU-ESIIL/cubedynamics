"""Publication checks for the retained CubeDynamics overview-manuscript PDFs."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_DIR = ROOT / "docs" / "documentation"

EXPECTED = {
    "cubedynamics-overview-manuscript.pdf": (
        252_765,
        "9980f5aaa83f3e38a72ea0d350a9675b3a22a54fc15f027ca02885c6d048adbf",
    ),
    "cubedynamics-overview-manuscript-supplement.pdf": (
        321_237,
        "ea8c3ea03ddf69c799b638f38e8f9f1b2211ab55b24db3e86decaca93831d09f",
    ),
}


def test_overview_manuscript_pdfs_preserve_supplied_bytes():
    for filename, (expected_size, expected_sha256) in EXPECTED.items():
        payload = (MANUSCRIPT_DIR / filename).read_bytes()
        assert len(payload) == expected_size
        assert hashlib.sha256(payload).hexdigest() == expected_sha256


def test_overview_manuscript_is_linked_package_wide():
    landing = (MANUSCRIPT_DIR / "overview_manuscript.md").read_text(encoding="utf-8")
    assert "CubeDynamics: An Inspectable Grammar for Environmental Data Analysis" in landing
    assert "25 September 2026" in landing
    for filename in EXPECTED:
        assert filename in landing

    assert "overview_manuscript.md" in (MANUSCRIPT_DIR / "index.md").read_text(encoding="utf-8")
    assert "documentation/overview_manuscript.md" in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for path in (
        ROOT / "docs" / "concepts" / "scientific_inspectability.md",
        ROOT / "docs" / "methods_and_citation.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "overview_manuscript.md" in text
        assert "main-17.pdf" not in text
