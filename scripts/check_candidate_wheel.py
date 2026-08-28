#!/usr/bin/env python3
"""Verify candidate modules and real replay from an installed, non-editable wheel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--package-root",type=Path,help="Optional isolated --target wheel installation")
    args=parser.parse_args()
    if args.package_root:
        sys.path.insert(0,str(args.package_root.resolve()))
    import cubedynamics
    from cubedynamics import pipe, verbs as v
    from cubedynamics.data import usgs, three_dep, roads, validate_source_promotion
    root=Path(__file__).resolve().parents[1]
    module=Path(cubedynamics.__file__).resolve()
    if module.is_relative_to(root/"src"):
        raise RuntimeError("Wheel check imported editable source instead of installed wheel")
    fixture=root/"tests/fixtures/real_data/usgs_streamflow"
    provenance=json.loads((fixture/"provenance.json").read_text())
    for name,site in provenance["sites"].items():
        cube=usgs.streamflow(site=site,start=provenance["start"],end=provenance["end"],
                             snapshot_dir=fixture/name,offline=True)
        assert (pipe(cube)|v.mean(dim="time")).unwrap().streamflow.item()>0
    assert callable(three_dep.elevation) and callable(roads.roads) and callable(validate_source_promotion)
    print(f"PASS: installed wheel candidate imports and three real snapshots: {module}")


if __name__=="__main__": main()
