"""Small experiment-only HTTP/evidence helpers, not another source framework."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import requests

from cubedynamics.data.certification import write_live_certification
from cubedynamics.data.lifecycle import CertificationRecord, CertificationOutcome as Outcome
from cubedynamics.version import __version__


class AccessBlocked(RuntimeError):
    """Anonymous service access prevented evaluation (not scientific failure)."""


def fetch(url, *, params=None, max_bytes=2_000_000, evidence=None, headers=None):
    """One anonymous, no-redirect, byte-capped GET. No retries or fallback."""
    trace = {"url": url, "params": params, "max_bytes": max_bytes, "bytes": 0,
             "anonymous": True, "retrieved_at": datetime.now(timezone.utc).isoformat()}
    if evidence is not None:
        evidence.append(trace)
    with requests.Session() as session:
        session.trust_env = False  # No environment proxies, netrc, keys or sessions.
        try:
            with session.get(url, params=params, headers={"Accept-Encoding": "identity",
                    "User-Agent": "CubeDynamics-source-proof/1", **(headers or {})},
                    timeout=(10, 40), stream=True, allow_redirects=False) as response:
                trace.update(url=response.url, status=response.status_code,
                             content_type=response.headers.get("Content-Type"),
                             headers={k: response.headers.get(k) for k in
                                      ("Content-Length", "Content-Range", "ETag", "Last-Modified", "Retry-After")})
                if response.status_code not in (200, 206):
                    raise AccessBlocked(f"HTTP {response.status_code} from {url}; no retry/fallback")
                if int(response.headers.get("Content-Length", 0)) > max_bytes:
                    raise ValueError("Response exceeds byte budget; body not read")
                chunks = []
                for chunk in response.iter_content(8192):
                    trace["bytes"] += len(chunk)
                    if trace["bytes"] > max_bytes:
                        raise ValueError("Response exceeds byte budget (at most one 8 KiB chunk over)")
                    chunks.append(chunk)
                content = b"".join(chunks)
                trace["sha256"] = hashlib.sha256(content).hexdigest()
                return content
        except requests.RequestException as exc:
            trace["error"] = str(exc)
            raise AccessBlocked(str(exc)) from exc


def json_get(url, **kwargs):
    return json.loads(fetch(url, **kwargs))


def save_report(output, *, gates, evidence, caveats=()):
    """Reuse the repository certification record/writer, with no fake revision."""
    gates = {k: Outcome(v) for k, v in gates.items()}
    if Outcome.FAIL in gates.values():
        outcome = Outcome.FAIL
    elif Outcome.BLOCKED in gates.values():
        outcome = Outcome.BLOCKED
    elif caveats or Outcome.NOT_TESTED in gates.values():
        outcome = Outcome.PASS_WITH_CAVEATS
    else:
        outcome = Outcome.PASS
    evidence["git_sha"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()
    evidence["uncommitted_changes_possible"] = True
    evidence["cubedynamics_version"] = __version__
    record = CertificationRecord(mode="live_source", outcome=outcome, gates=gates,
        serving_revision=None, last_validated=datetime.now(timezone.utc).isoformat(),
        evidence=evidence, caveats=tuple(caveats))
    result = {"lifecycle_state": "candidate", "registered": False,
              "live_health": "unavailable" if outcome is Outcome.BLOCKED else
                             "degraded" if outcome is Outcome.FAIL else "healthy",
              "certification": record.as_dict()}
    write_live_certification(result, Path(output))
    return result
