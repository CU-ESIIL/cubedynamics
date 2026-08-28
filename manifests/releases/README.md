# Release Manifests

Place small published manifest snapshots here when they are intentionally part
of a reproducible release. Do not commit bulk processing manifests or generated
lakehouse tables.

`v0.1.0-candidate.json` is a pre-publication review record, not a tag, DOI or
serving revision. `scripts/run_release_gate.py` uses the existing
`source_lifecycle_evidence.release_manifest` inventory and adds wheel/sdist
hashes, installed-wheel notebook evidence, tested Python/platform, command
results and explicit caveats. Base commit and working-tree overlay are distinct.
The manifest excludes its own bytes from that overlay to avoid a self-hash loop.
Logs and executed notebooks remain under ignored `artifacts/release-0.1.0/`.
`--record-only` refuses missing/failed gates or changed release inputs/artifacts.
