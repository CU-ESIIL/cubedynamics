"""Fault injection controls, never substitutes for real scientific fixtures."""
import hashlib
import json

import pytest
import requests

from cubedynamics.data import _transport as t


class Response:
    status_code = 200
    headers = {}
    chunks = [b'{"ok":true}']

    def __enter__(self): return self
    def __exit__(self, *args): pass
    def iter_content(self, size): yield from self.chunks


@pytest.fixture
def transport(monkeypatch):
    calls, responses, delays = [], [], []
    class Session:
        trust_env = True
        def close(self): pass
        def get(self, url, **kwargs):
            assert not self.trust_env and not kwargs["allow_redirects"]
            calls.append((url, kwargs))
            result = responses.pop(0)
            if isinstance(result, Exception): raise result
            return result
    monkeypatch.setattr(t.requests, "Session", Session)
    monkeypatch.setattr(t.time, "sleep", delays.append)
    return calls, responses, delays


def client(**kwargs):
    return t.SourceClient(origins={"https://example.test"}, **kwargs)


def response(status=200, **headers):
    r = Response()
    r.status_code, r.headers = status, headers
    return r


def test_retry_after_and_attempt_evidence(transport):
    calls, responses, delays = transport
    responses.extend([response(429, **{"Retry-After": "2"}), response()])
    with client() as c:
        assert c.json("https://example.test/data") == {"ok": True}
        assert [x["status"] for x in c.trace] == [429, 200]
    assert len(calls) == 2 and delays == [2]


@pytest.mark.parametrize("status,kind", [(302,t.SourceAccessError),(401,t.SourceAccessError),
    (403,t.SourceAccessError),(404,t.SourceRequestError),(400,t.SourceRequestError)])
def test_permanent_errors_are_not_retried(transport,status,kind):
    calls, responses, _ = transport
    responses.append(response(status))
    with client() as c, pytest.raises(kind): c.get("https://example.test/data")
    assert len(calls) == 1


def test_retry_request_budget(transport):
    calls, responses, _ = transport
    responses.extend([response(503)] * 3)
    with client(limits=t.ReadLimits(requests=2)) as c, pytest.raises(t.SourceBudgetError):
        c.get("https://example.test/data")
    assert len(calls) == 2


def test_connection_timeout_retries_are_bounded(transport):
    calls, responses, _ = transport
    responses.extend([requests.Timeout()] * 3)
    with client() as c, pytest.raises(t.SourceUnavailable): c.get("https://example.test/data")
    assert len(calls) == 3


def test_retry_after_never_violates_provider_delay(transport):
    calls, responses, delays = transport
    responses.append(response(429, **{"Retry-After": "9999"}))
    with client() as c, pytest.raises(t.SourceBudgetError): c.get("https://example.test/data")
    assert len(calls) == 1 and delays == []


@pytest.mark.parametrize("url", ["http://example.test/x", "https://evil.test/x",
    "https://user:password@example.test/x", "https://example.test/x#part"])
def test_unapproved_url_rejected_before_request(transport,url):
    with client() as c, pytest.raises(t.SourceAccessError): c.get(url)
    assert transport[0] == []


def test_byte_budget_aggregates_requests_and_refuses_announced_oversize(transport):
    calls, responses, _ = transport
    responses.extend([response(), response(200, **{"Content-Length": "11"})])
    with client(limits=t.ReadLimits(bytes=20)) as c:
        c.get("https://example.test/a")
        with pytest.raises(t.SourceBudgetError): c.get("https://example.test/b")
        assert c.bytes == 11


def test_unannounced_oversize_charged_and_recorded(transport):
    transport[1].append(response())
    with client(limits=t.ReadLimits(bytes=4)) as c:
        with pytest.raises(t.SourceBudgetError): c.get("https://example.test/a")
        assert c.bytes == 11 and c.trace[-1]["bytes"] == 11


def test_snapshot_is_exact_immutable_and_replay_never_networks(transport,tmp_path):
    transport[1].append(response())
    with client(snapshot_dir=tmp_path) as c:
        raw = c.get("https://example.test/data", params={"site": "a"})
    digest = hashlib.sha256(raw).hexdigest()
    assert (tmp_path/"bodies"/f"{digest}.bin").read_bytes() == raw
    with client(snapshot_dir=tmp_path,offline=True) as c:
        assert c.get("https://example.test/data", params={"site":"a"}) == raw
        assert c.trace[-1]["cache"] == "offline"
        with pytest.raises(t.SourceSchemaError): c.get("https://example.test/missing")
    with client(snapshot_dir=tmp_path) as c, pytest.raises(t.SourceRequestError):
        c.get("https://example.test/data",params={"site":"a"})
    assert len(transport[0]) == 1
    (tmp_path/"bodies"/f"{digest}.bin").write_bytes(b"corrupt")
    with client(snapshot_dir=tmp_path,offline=True) as c, pytest.raises(t.SourceSchemaError):
        c.get("https://example.test/data",params={"site":"a"})


def test_malformed_json_and_truncated_body(transport):
    r=response(); r.chunks=[b"<html>maintenance</html>"]
    transport[1].append(r)
    with client() as c, pytest.raises(t.SourceSchemaError): c.json("https://example.test/data")
    transport[1].append(response(200, **{"Content-Length":"100"}))
    with client() as c, pytest.raises(t.SourceSchemaError): c.get("https://example.test/data")


@pytest.mark.parametrize("kw", [{"attempts":0},{"seconds":float("inf")},{"bytes":-1},{"requests":1.5}])
def test_invalid_limits(kw):
    with pytest.raises(ValueError): t.ReadLimits(**kw)
