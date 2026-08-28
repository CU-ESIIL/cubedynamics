"""Scientific nouns and source-specific loading helpers.

Use noun functions such as :func:`temperature` in new analyses.  The
``load_*`` functions remain public for workflows that deliberately need a
provider-specific product.
"""

from .catalog import describe, list_sources, sources
from .certification import (
    blocked_live_certification,
    certify_live_sample,
    write_live_certification,
)
from .gridmet import load_gridmet_cube
from .lifecycle import (
    CertificationOutcome,
    CertificationRecord,
    LiveHealth,
    RevisionStatus,
    RevisionStage,
    ServingRevision,
    ServingRevisionRecord,
    SourceChange,
    SourceMode,
    UpstreamIdentity,
    decide_source_change,
)
from .nouns import (
    humidity,
    precipitation,
    radiation,
    surface_reflectance,
    temperature,
    vegetation_index,
    vpd,
    wind,
)
from .prism import load_prism_cube
from .qa import evaluate_qa_profile, get_qa_profile, list_qa_profiles
from .revisions import (
    current_revision_record,
    rollback_target,
    serving_history,
    validate_promotion,
    validate_source_promotion,
)
from .schema import (
    compare_normalized_schemas,
    fingerprint_normalized_schema,
    normalize_api_schema,
    normalize_vector_schema,
    normalize_xarray_schema,
    schema_fingerprint,
)
from .sentinel2 import load_s2_cube, load_s2_ndvi_cube

__all__ = [
    "describe",
    "CertificationOutcome",
    "CertificationRecord",
    "blocked_live_certification",
    "certify_live_sample",
    "humidity",
    "list_sources",
    "list_qa_profiles",
    "LiveHealth",
    "load_gridmet_cube",
    "load_prism_cube",
    "load_s2_cube",
    "load_s2_ndvi_cube",
    "precipitation",
    "radiation",
    "RevisionStatus",
    "RevisionStage",
    "ServingRevision",
    "ServingRevisionRecord",
    "SourceChange",
    "SourceMode",
    "sources",
    "surface_reflectance",
    "temperature",
    "UpstreamIdentity",
    "vegetation_index",
    "vpd",
    "wind",
    "write_live_certification",
    "compare_normalized_schemas",
    "current_revision_record",
    "decide_source_change",
    "evaluate_qa_profile",
    "get_qa_profile",
    "fingerprint_normalized_schema",
    "normalize_api_schema",
    "normalize_vector_schema",
    "normalize_xarray_schema",
    "rollback_target",
    "schema_fingerprint",
    "serving_history",
    "validate_promotion",
    "validate_source_promotion",
]
