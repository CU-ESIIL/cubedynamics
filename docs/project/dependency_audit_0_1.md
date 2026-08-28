# Dependency audit for 0.1

Release-hardening review, 28 August 2026. **No runtime dependencies were moved
or removed.** A small conceptual grammar does not currently mean a small
installation: the top-level namespace imports the shared vocabulary, source
helpers and project compatibility paths. Moving packages to extras without
changing those imports would break normal installs.

The classification describes ownership, not proof that importing `pipe` can
avoid a dependency in this distribution.

| Base dependency | Classification | Current reason / boundary |
| --- | --- | --- |
| numpy | Core required | Array numerical semantics and vocabulary |
| xarray | Core required | Labeled objects, dimensions, attrs |
| pandas | Core required | Time/index/tabular handling underlying labeled data |
| dask | Core required | Documented deferred array workflows and VirtualCube integration |
| rasterio | Common integration | Raster IO and CRS/grid operations; installed 3DEP requires >=1.4 at use time |
| rioxarray | Common integration | Spatial xarray accessor and raster methods |
| pystac-client | Common integration | STAC data discovery |
| planetary-computer | Common integration | Satellite asset signing and source integration |
| pyproj | Common integration | Coordinate transforms and CRS contracts |
| requests | Common integration | Provider HTTP and bounded candidate transport |
| h5netcdf | Common integration | NetCDF reading/writing backend |
| h5py | Common integration | HDF5 backend support |
| cubo | Common integration | Satellite cube construction |
| matplotlib | Common integration | Plots; imported by the verb namespace |
| Pillow | Common integration | Viewer textures and figure validation |
| crc32c | Common integration (declared legacy dependency) | No direct runtime import found; not needed by the core grammar. Retained pending a deliberate dependency-removal review. |
| plotly | Project-specific | Fire/VASE rendering and legacy plotting; not the canonical HTML cube viewer |
| geopandas | Common integration | Spatial operations, biology/fire and candidate vector data |
| shapely | Common integration | Geometry semantics across project/spatial APIs |
| scipy | Common integration | Numerical/spatial helpers and NetCDF3 fixture backend |
| ipython | Common integration | Notebook/display protocol; imported by the verb namespace |

## Existing extras

- **Optional candidate:** `roads` adds PyArrow >=17,<22 only at Overture access.
  Exact offline GeoJSON lessons need no PyArrow. Do not infer all base Rasterio
  versions support the bounded 3DEP decoder; its use-time check is intentional.
- **Common optional visualization:** `viz` adds Lexcube; the canonical HTML
  viewer is already shipped and does not require it.
- **Docs/dev only:** `test` (pytest, build, twine), `docs` (MkDocs, plugins,
  nbclient, nbformat), `vignettes` (nbclient, nbformat, ipykernel), `browser`
  (Playwright and pytest plugin, Python >=3.10), and combined `dev`.
- Live gridMET OPeNDAP can need an additional netCDF4/pydap backend. The annual
  HTTPS fallback is not equivalent bounded chunk access.

## Release decisions and 0.2 recommendations

Keep the existing import/dependency surface for compatibility. The clean-wheel
test first installs the wheel and declared base dependencies only, then adds
the documented vignette extra for notebook kernels. `pip check` and the
recorded environment inventory establish the tested resolution; they do not
prove every possible older dependency combination.

For 0.2, measure import cost and make renderer/provider/project imports lazy
before moving dependencies. Add lower-bound and multi-platform install tests,
define optional NetCDF/decoder groups, and review version constraints using
real compatibility evidence. Review the apparently unused crc32c declaration
for removal with clean-install compatibility tests. Preserve the current NumPy <2 guard and PyArrow
range rather than loosening them during release preparation. The existing
setuptools license-table deprecation is a future packaging migration, not a
reason to silently raise the build-system floor in this pass.

[Release notes](release_0_1_0.md) · [0.1 API support](api_support_0_1.md)
