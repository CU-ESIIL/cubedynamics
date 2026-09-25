"""Publication checks for the retained synchrony technical-report PDFs."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "synchrony"

EXPECTED = {
    "spatial-organization-cold-warm-temperature-synchrony.pdf": (
        2_415_877,
        "c65743903d182627fd792055c554eba24277aba6e8f5db3072d3d816e35c32a9",
    ),
    "spatial-organization-cold-warm-temperature-synchrony-supplement.pdf": (
        4_007_076,
        "52d31187b75e15bbe67477bb5532438876a4f1c51be170820cc0183c2f421cc4",
    ),
}


def test_synchrony_report_pdfs_preserve_supplied_bytes():
    for filename, (expected_size, expected_sha256) in EXPECTED.items():
        payload = (REPORT_DIR / filename).read_bytes()
        assert len(payload) == expected_size
        assert hashlib.sha256(payload).hexdigest() == expected_sha256


def test_synchrony_report_landing_page_links_both_pdfs():
    text = (REPORT_DIR / "technical_report.md").read_text(encoding="utf-8")
    assert "The Spatial Organization of Cold and Warm Temperature Synchrony" in text
    assert "25 September 2026" in text
    for filename in EXPECTED:
        assert filename in text
