import json
import pytest
from cubedynamics.data.lifecycle import CertificationRecord, CertificationOutcome
from examples.source_projects import _evidence as evidence


def test_pre_registration_certification_does_not_invent_a_revision():
    record=CertificationRecord(mode="live_source",outcome=CertificationOutcome.BLOCKED,
        gates={"retrieval":CertificationOutcome.BLOCKED},serving_revision=None,last_validated="2026-08-27")
    assert json.loads(json.dumps(record.as_dict()))["serving_revision"] is None


def test_invalid_non_null_revision_still_rejected():
    with pytest.raises(ValueError,match="Serving revision"):
        CertificationRecord(mode="live_source",outcome=CertificationOutcome.BLOCKED,
            gates={"retrieval":CertificationOutcome.BLOCKED},serving_revision="made up",last_validated="2026-08-27")


class Response:
    url="https://example.test/data"
    status_code=200
    headers={}
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def iter_content(self,size): yield b"12345"


class Session:
    trust_env=True
    response=Response()
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def get(self,url,**kwargs):
        assert self.trust_env is False
        assert kwargs["allow_redirects"] is False
        return self.response


def test_fetch_refuses_oversize_and_records_attempt(monkeypatch):
    monkeypatch.setattr(evidence.requests,"Session",Session)
    trace=[]
    with pytest.raises(ValueError,match="budget"):
        evidence.fetch(Response.url,max_bytes=4,evidence=trace)
    assert trace[0]["bytes"]==5


@pytest.mark.parametrize("status",[302,401,403,429,503])
def test_fetch_never_follows_login_or_retries(monkeypatch,status):
    response=Response()
    response.status_code=status
    monkeypatch.setattr(Session,"response",response)
    monkeypatch.setattr(evidence.requests,"Session",Session)
    with pytest.raises(evidence.AccessBlocked,match=str(status)):
        evidence.fetch(Response.url)
