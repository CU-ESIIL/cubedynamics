# Data and source configuration

[Noun definitions and source facts](../library/index.md) live in Library.
This page documents discovery, loading, provenance, schema and QA functions.
Signatures and descriptions below come from the runtime docstrings.

## Discovery

::: cubedynamics.data.catalog
    options:
      members: [list_sources, sources, describe]
      show_docstring_examples: false

## Temporal support

Time labels and physical observation intervals are separate metadata. See the
[Temporal alignment guide](../concepts/temporal_alignment.md).

::: cubedynamics.temporal
    options:
      members: [TemporalSupport, TemporalAlignmentReport, temporal_support, observation_intervals, compare_temporal_support]
      show_docstring_examples: false

## Source-specific loaders

Provider-specific loaders remain supported alongside scientific nouns.
[Compare implemented source flavors](../library/sources/index.md) before choosing.

::: cubedynamics.data.gridmet.load_gridmet_cube
    options:
      show_docstring_examples: false

::: cubedynamics.data.prism.load_prism_cube
    options:
      show_docstring_examples: false

::: cubedynamics.data.sentinel2
    options:
      members: [load_s2_cube, load_s2_ndvi_cube]
      show_docstring_examples: false

## Serving revisions

::: cubedynamics.data.revisions
    options:
      members: [serving_history, current_revision_record, validate_promotion, rollback_target]

## Lifecycle decisions and records

::: cubedynamics.data.lifecycle
    options:
      members: [ServingRevision, ServingRevisionRecord, UpstreamIdentity, CertificationRecord, decide_source_change]

## Schema normalization

::: cubedynamics.data.schema
    options:
      members: [normalize_xarray_schema, normalize_vector_schema, normalize_api_schema, schema_fingerprint, fingerprint_normalized_schema, compare_normalized_schemas]

## QA and certification

::: cubedynamics.data.qa
    options:
      members: [list_qa_profiles, get_qa_profile, evaluate_qa_profile]

::: cubedynamics.data.certification
    options:
      members: [certify_live_sample, blocked_live_certification, write_live_certification]

## See also

[Source lifecycle contract](../dev/source_lifecycle.md) · [Source QA evidence](../data/phase1_qa.md) ·
[Legacy semantic helpers](../project/public_api.md) · [Provenance lesson](../learn/provenance.md)
