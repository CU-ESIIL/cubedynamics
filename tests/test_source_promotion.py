"""Production release gates bind actual artifacts, not an outcome string."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib

import pytest

from cubedynamics.data.lifecycle import CertificationRecord, ServingRevisionRecord
from cubedynamics.data.revisions import validate_source_promotion, PRODUCTION_GATES


@pytest.fixture
def evidence(tmp_path):
    (tmp_path/"qa.json").write_bytes(b'{"reviewed":true}')
    candidate=ServingRevisionRecord(revision_id="streamflow.usgs@2026-08-27.1",stage="CANDIDATE",
        status="VALIDATED",created_at="2026-08-27T00:00:00Z",adapter_version="adapter-sha",
        schema_fingerprint="sha256:schema",qa_evidence="qa.json",normalization_contract="contract-v1")
    cert=CertificationRecord(mode="offline_baseline",outcome="PASS_WITH_CAVEATS",serving_revision=candidate.revision_id,
        last_validated="2026-08-27T00:00:00Z",gates={k:"PASS" for k in PRODUCTION_GATES},
        evidence={"noun":"streamflow","source_flavor":"usgs","adapter_version":"adapter-sha",
            "normalization_contract":"contract-v1","schema_fingerprint":"sha256:schema",
            "supported_scope":"one station, bounded window","reviewer":"unit-test control, not real review",
            "artifact_sha256":{"qa.json":hashlib.sha256((tmp_path/"qa.json").read_bytes()).hexdigest()}})
    return candidate,cert


def validate(evidence,tmp_path):
    validate_source_promotion(*evidence,artifact_root=tmp_path,now=datetime(2026,8,28,tzinfo=timezone.utc))


def test_exact_candidate_and_artifacts_pass_without_mutation(evidence,tmp_path):
    validate(evidence,tmp_path)
    assert evidence[0].stage.value=="CANDIDATE"


@pytest.mark.parametrize("gate",sorted(PRODUCTION_GATES))
def test_every_required_gate_must_explicitly_pass(evidence,tmp_path,gate):
    candidate,cert=evidence
    gates={**cert.gates,gate:"NOT_TESTED"}
    with pytest.raises(ValueError,match="gates"):
        validate((candidate,replace(cert,gates=gates)),tmp_path)


@pytest.mark.parametrize("field",["noun","source_flavor","adapter_version","normalization_contract","schema_fingerprint"])
def test_mismatched_identity_rejected(evidence,tmp_path,field):
    candidate,cert=evidence
    with pytest.raises(ValueError,match=field):
        validate((candidate,replace(cert,evidence={**cert.evidence,field:"wrong"})),tmp_path)


def test_artifact_tampering_rejected(evidence,tmp_path):
    (tmp_path/"qa.json").write_bytes(b"modified")
    with pytest.raises(ValueError,match="checksum"): validate(evidence,tmp_path)


@pytest.mark.parametrize("date",["2020-01-01T00:00:00Z","2027-01-01T00:00:00Z","2026-08-27"])
def test_stale_future_or_naive_certification_rejected(evidence,tmp_path,date):
    with pytest.raises(ValueError,match="timestamp"):
        validate((evidence[0],replace(evidence[1],last_validated=date)),tmp_path)


def test_wrong_revision_and_escape_rejected(evidence,tmp_path):
    candidate,cert=evidence
    with pytest.raises(ValueError,match="different serving"):
        validate((candidate,replace(cert,serving_revision="streamflow.usgs@2026-08-26.1")),tmp_path)
    cert=replace(cert,evidence={**cert.evidence,"artifact_sha256":{"../qa.json":"a"*64}})
    with pytest.raises(ValueError,match="escapes"):
        validate((replace(candidate,qa_evidence="../qa.json"),cert),tmp_path)
