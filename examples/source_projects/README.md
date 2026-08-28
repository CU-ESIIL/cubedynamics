# Three contained source projects

These projects use CubeDynamics' ordinary noun → `pipe` → callable verb model,
its QA profiles, schema fingerprints and certification records. They are not
new production catalog entries. Install the repo editable and run from its root.
Raw samples and diagnostics stay under ignored `artifacts/source_qa/`.

1. **[3DEP](three_dep/proof.py)**: one catalog-discovered, bounded 2-D terrain
   window. `python -m examples.source_projects.three_dep.proof`
2. **[Roads](roads/proof.py)**: independent Overture/OSM reads, common conservative
   noun, explicit comparison. Install optional `roads/requirements.txt`, then
   `python -m examples.source_projects.roads.proof`.
3. **[USGS](usgs/proof.py)**: one-site, ≤3-day modern OGC streamflow noun.
   `python -m examples.source_projects.usgs.proof`

Each command performs bounded **online** requests, creates real-data plots and
writes existing `CertificationRecord` evidence. It does not publish, promote,
authenticate, use synthetic fallback, or fetch a whole raster/global vector
dataset. Run offline tests with:

```bash
python -m pytest tests/test_source_project_*.py -m "not integration and not online" -q
```

Opt-in live tests: replace the marker expression with `online`. Provider outage
fails the live test honestly; the command reports BLOCKED rather than inventing
observations. The separate Daymet experiment remains blocked at authentication.

Project nouns are explicit consuming loaders (bounded eager samples). The pipe
does not magically make network requests lazy. Static terrain has no invented
time dimension; roads are GeoDataFrames, not raster cubes; streamflow is a
`time × station` Dataset. Use only verbs whose input contracts match.

The [website reports](../../docs/data/source_projects/index.md) include architecture
reviews and limits. `scripts/build_source_project_docs.py` exports reviewed
evidence; its `--check` mode works offline in fresh clones. `--review` must follow
actual inspection and records figure hashes, not an automatic approval.

The manual GitHub Actions **Bounded Source Projects** workflow runs each project
in an independent job and uploads its evidence even on failure. It does not
auto-approve figures or register/promote sources. The regular offline/docs
pipeline checks the committed, reviewed publication evidence without network.
