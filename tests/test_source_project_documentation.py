from pathlib import Path
import shutil
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import build_source_project_docs as builder
import docs_hooks


def test_published_project_evidence_and_reviews_are_current():
    builder.check()


def test_generated_library_nav_promotes_nouns_not_project_reports():
    config={"docs_dir":str(builder.ROOT/"docs"),"nav":[{"Library":[
        {"Experimental source projects":[{"Three projects":"data/source_projects/index.md"}]}]}]}
    result=docs_hooks.on_config(config)
    entries = result["nav"][0]["Library"]
    assert not any("Experimental source projects" in item for item in entries)
    for noun in ("elevation", "roads", "streamflow"):
        assert f"library/nouns/{noun}.md" in str(entries)


def test_changed_scientific_figure_fails_publication_check(tmp_path,monkeypatch):
    asset=tmp_path/"docs/assets/generated/source_projects"
    shutil.copytree(builder.ASSETS,asset)
    page=tmp_path/"docs/data/source_projects/evidence.md"
    page.parent.mkdir(parents=True)
    shutil.copyfile(builder.PAGE,page)
    monkeypatch.setattr(builder,"ROOT",tmp_path)
    monkeypatch.setattr(builder,"ASSETS",asset)
    monkeypatch.setattr(builder,"PAGE",page)
    (asset/"terrain.png").write_bytes(b"not the reviewed figure")
    with pytest.raises(ValueError,match="Stale"):
        builder.check()
