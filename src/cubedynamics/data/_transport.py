"""Bounded anonymous source reads and explicit, content-addressed replay.

Internal adapter infrastructure, not a general HTTP client. Limits include all
attempts and decoded response bytes (not TCP/TLS overhead). No credentials,
redirects, implicit cache writes, synthetic fallback, or unbounded retries.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import math
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

import requests


class SourceError(RuntimeError):
    """A source read could not meet its documented contract."""


class SourceUnavailable(SourceError):
    """Transient transport failure or unavailable provider."""


class SourceAccessError(SourceError):
    """Authentication, forbidden access, or an unexpected redirect."""


class SourceRequestError(SourceError, ValueError):
    """Invalid scope or a provider-rejected request."""


class SourceSchemaError(SourceError, ValueError):
    """Malformed, incomplete, or semantically inconsistent source content."""


class SourceBudgetError(SourceError, ValueError):
    """A bounded query exceeded a request, byte, row, or time limit."""


@dataclass(frozen=True)
class ReadLimits:
    """Per-loader limits, including retries; deadlines checked between reads."""

    requests: int = 40
    bytes: int = 16_000_000
    seconds: float = 180
    attempts: int = 3
    read_timeout: float = 20

    def __post_init__(self):
        for name in ("requests", "bytes", "attempts"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("seconds", "read_timeout"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive and finite")


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class SourceClient:
    """One synchronous query budget. Use as a context manager.

    ``snapshot_dir`` explicitly saves raw successful bodies and request records.
    Existing request records are immutable: a refresh needs a new directory.
    ``offline=True`` reads only that snapshot and verifies every content hash.
    Partial snapshots may be retained after failure, but no partial noun is
    returned. This client is deliberately not thread-safe.
    """

    def __init__(self, *, origins, limits=None, snapshot_dir=None, offline=False):
        self.origins = frozenset(origins)
        self.limits = limits or ReadLimits()
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir is not None else None
        self.offline = offline
        if offline and self.snapshot_dir is None:
            raise ValueError("Offline replay requires snapshot_dir")
        self.trace = []
        self.bytes = self.requests = 0
        self.started = time.monotonic()
        self.session = None
        self._memo = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.session is not None:
            self.session.close()

    def _remaining(self):
        remaining = self.limits.seconds - (time.monotonic() - self.started)
        if remaining <= 0:
            raise SourceBudgetError("Source query deadline exceeded")
        return remaining

    def _validate_url(self, url):
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.username or parts.password or parts.fragment
                or f"{parts.scheme}://{parts.netloc}" not in self.origins):
            raise SourceAccessError("Source URL is not an approved anonymous HTTPS origin")

    def _request(self, url, params, headers):
        self._validate_url(url)
        # Keys/authorization are intentionally unsupported in this anonymous API.
        allowed = {"Range", "If-Match"}
        if set(headers) - allowed:
            raise SourceRequestError("Only Range and If-Match custom headers are supported")
        if any(re.search(r"key|token|password|secret", str(k), re.I) for k in (params or {})):
            raise SourceRequestError("Credentials are not supported by this source client")
        prepared = requests.Request("GET", url, params=params).prepare().url
        return {"url": prepared, "headers": headers}

    def _snapshot_paths(self, request):
        key = hashlib.sha256(_json_bytes(request)).hexdigest()
        return self.snapshot_dir / "requests" / f"{key}.json"

    def _replay(self, request, cap):
        path = self._snapshot_paths(request)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            digest = record["sha256"]
            if record["request"] != request or not re.fullmatch(r"[a-f0-9]{64}", digest):
                raise ValueError("Snapshot identity mismatch")
            blob = self.snapshot_dir / "bodies" / f"{digest}.bin"
            if blob.stat().st_size > cap:
                raise SourceBudgetError("Snapshot exceeds response byte budget")
            raw = blob.read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest or len(raw) != record["bytes"]:
                raise ValueError("Snapshot checksum mismatch")
        except SourceBudgetError:
            raise
        except (OSError, KeyError, ValueError) as exc:
            raise SourceSchemaError(f"Missing or invalid snapshot: {path.name}: {exc}") from exc
        self.bytes += len(raw)
        self.trace.append({**record, "cache": "offline", "replayed_at": datetime.now(timezone.utc).isoformat()})
        return raw

    def _save(self, request, raw, record):
        if self.snapshot_dir is None:
            return
        path = self._snapshot_paths(request)
        blob = self.snapshot_dir / "bodies" / f"{record['sha256']}.bin"
        path.parent.mkdir(parents=True, exist_ok=True)
        blob.parent.mkdir(parents=True, exist_ok=True)
        # Never replace the snapshot used by an earlier analysis.
        if path.exists():
            raise SourceRequestError("Snapshot request already exists; use offline=True or a new directory")
        try:
            with blob.open("xb") as stream:
                stream.write(raw)
        except FileExistsError:
            if hashlib.sha256(blob.read_bytes()).hexdigest() != record["sha256"]:
                raise SourceSchemaError("Existing snapshot body is corrupt")
        with path.open("x", encoding="utf-8") as stream:
            json.dump({**record, "request": request}, stream, sort_keys=True, indent=2)

    def get(self, url, *, params=None, max_bytes=2_000_000, headers=None):
        """Return exact uncompressed bytes; all failures preserve an attempt trace."""
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive integer")
        headers = dict(headers or {})
        request = self._request(url, params, headers)
        memo_key = _json_bytes(request)
        if memo_key in self._memo:
            raw, record = self._memo[memo_key]
            if len(raw) > max_bytes:
                raise SourceBudgetError("Cached response exceeds requested byte budget")
            self._remaining()
            self.trace.append({**record, "cache": "query_memory"})
            return raw
        cap = min(max_bytes, self.limits.bytes - self.bytes)
        self._remaining()
        if cap <= 0:
            raise SourceBudgetError("Source byte budget exhausted")
        if self.offline:
            if self.requests >= self.limits.requests:
                raise SourceBudgetError("Source request budget exhausted")
            self.requests += 1
            raw = self._replay(request, cap)
            self._memo[memo_key] = (raw, self.trace[-1])
            return raw
        if self.snapshot_dir and self._snapshot_paths(request).exists():
            raise SourceRequestError("Snapshot request already exists; use offline=True or a new directory")
        if self.session is None:
            self.session = requests.Session()
            self.session.trust_env = False
        for attempt in range(self.limits.attempts):
            if self.requests >= self.limits.requests:
                raise SourceBudgetError("Source request budget exhausted (including retries)")
            self.requests += 1
            trace = {"request": request, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                     "bytes": 0, "attempt": attempt + 1, "cache": "network"}
            self.trace.append(trace)
            delay = min(2 ** attempt, 8)
            try:
                timeout = min(self.limits.read_timeout, self._remaining())
                with self.session.get(request["url"], headers={"Accept-Encoding": "identity",
                        "User-Agent": "CubeDynamics-bounded-source/1", **headers}, stream=True,
                        timeout=(min(10, timeout), timeout), allow_redirects=False) as response:
                    status = response.status_code
                    trace.update(status=status, headers={k: response.headers.get(k) for k in
                        ("Content-Type", "Content-Length", "Content-Range", "ETag", "Last-Modified", "Retry-After")})
                    if status in (429, 500, 502, 503, 504):
                        retry = response.headers.get("Retry-After")
                        if retry:
                            try:
                                delay = max(0, float(retry))
                            except ValueError:
                                try:
                                    delay = max(0, (parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds())
                                except (TypeError, ValueError):
                                    pass
                        raise SourceUnavailable(f"Provider returned HTTP {status}")
                    if status in (401, 403) or 300 <= status < 400:
                        raise SourceAccessError(f"Provider returned HTTP {status}; no redirect/authentication fallback")
                    if status not in (200, 206):
                        raise SourceRequestError(f"Provider returned HTTP {status}")
                    if response.headers.get("Content-Encoding", "identity") not in ("identity", ""):
                        raise SourceSchemaError("Unexpected compressed body; exact byte accounting unavailable")
                    cap = min(max_bytes, self.limits.bytes - self.bytes)
                    if int(response.headers.get("Content-Length", 0)) > cap:
                        raise SourceBudgetError("Response exceeds byte budget before body read")
                    chunks = []
                    # A lying/missing length can overrun by <= one 8 KiB chunk.
                    # Bytes received on failed attempts also consume the budget.
                    for chunk in response.iter_content(8192):
                        self.bytes += len(chunk)
                        trace["bytes"] += len(chunk)
                        self._remaining()
                        if trace["bytes"] > max_bytes or self.bytes > self.limits.bytes:
                            raise SourceBudgetError("Response exceeds byte budget (<=8 KiB detection granularity)")
                        chunks.append(chunk)
                    raw = b"".join(chunks)
                    length = response.headers.get("Content-Length")
                    if length is not None and len(raw) != int(length):
                        raise SourceSchemaError("Truncated response body")
                    trace["sha256"] = hashlib.sha256(raw).hexdigest()
                    self._save(request, raw, trace)
                    self._memo[memo_key] = (raw, trace.copy())
                    return raw
            except (requests.RequestException, SourceUnavailable) as exc:
                trace["error"] = type(exc).__name__
                if attempt + 1 >= self.limits.attempts:
                    raise SourceUnavailable(f"Source unavailable after {attempt + 1} attempts") from exc
                if not math.isfinite(delay) or delay >= self._remaining():
                    raise SourceBudgetError("Retry-After exceeds query deadline") from exc
                time.sleep(delay)
            except (SourceError, ValueError) as exc:
                trace["error"] = type(exc).__name__
                raise
        raise AssertionError("Unreachable retry state")

    def json(self, url, **kwargs):
        raw = self.get(url, **kwargs)
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise SourceSchemaError("Provider response is not JSON") from exc
        if not isinstance(value, dict):
            raise SourceSchemaError("Expected a JSON object")
        return value
