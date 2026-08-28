"""Strict byte-range file adapter shared by bounded raster/vector candidates."""
from __future__ import annotations

import io
import re

from ._transport import SourceSchemaError, SourceBudgetError


class RangeFile(io.RawIOBase):
    """Seekable read-only remote file; never downloads an entire object.

    Strong ETag + If-Match bind every read to the probed object. No ETag means
    no safe range assembly. Multipart ETags are identities, not content hashes.
    The client's query-wide budget counts retries and all objects/metadata.
    """

    def __init__(self, url, client):
        self.url, self.client, self.position = url, client, 0
        self._prefetched = None
        raw = client.get(url, headers={"Range": "bytes=0-0"}, max_bytes=1)
        trace = client.trace[-1]
        match = re.fullmatch(r"bytes 0-0/(\d+)", trace["headers"].get("Content-Range") or "")
        self.etag = trace["headers"].get("ETag")
        if trace["status"] != 206 or len(raw) != 1 or not match:
            raise SourceSchemaError("Source did not honor range probe")
        if not self.etag or self.etag.startswith("W/"):
            raise SourceSchemaError("Range assembly requires a strong object ETag")
        self.size = int(match[1])
        if self.size <= 1:
            raise SourceSchemaError("Invalid remote object size")

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence not in (io.SEEK_SET, io.SEEK_CUR, io.SEEK_END):
            raise ValueError("Invalid seek origin")
        position = offset if whence == io.SEEK_SET else self.position + offset if whence == io.SEEK_CUR else self.size + offset
        if not 0 <= position <= self.size:
            raise ValueError("Invalid seek position")
        self.position = position
        return position

    def read(self, size=-1):
        if self.closed:
            raise ValueError("Read on closed range file")
        if size < 0 or size >= self.size:
            raise SourceBudgetError("Whole-object/unbounded read refused")
        size = min(size, self.size - self.position)
        if size == 0:
            return b""
        if self._prefetched is not None:
            offset, raw = self._prefetched
            if offset <= self.position and self.position + size <= offset + len(raw):
                result = raw[self.position-offset:self.position-offset+size]
                self.position += size
                return result
        if size > self.client.limits.bytes - self.client.bytes:
            raise SourceBudgetError("Range exceeds remaining byte budget before request")
        start, end = self.position, self.position + size - 1
        raw = self.client.get(self.url, headers={"Range": f"bytes={start}-{end}", "If-Match": self.etag}, max_bytes=size)
        trace = self.client.trace[-1]
        if (trace["status"] != 206 or len(raw) != size
                or trace["headers"].get("Content-Range") != f"bytes {start}-{end}/{self.size}"
                or trace["headers"].get("ETag") != self.etag):
            raise SourceSchemaError("Changed object or incorrect/short range response")
        self.position += size
        return raw

    def prefetch(self, start, size):
        """Fetch one explicit contiguous row-group span; budget still enforced.

        PyArrow otherwise issues one request for each tiny nested column chunk.
        Only one span is retained here; the total client memo is byte-bounded.
        """
        position = self.position
        self._prefetched = None
        self.seek(start)
        raw = self.read(size)
        self._prefetched = (start, raw)
        self.seek(position)

    def readinto(self, buffer):
        raw = self.read(len(buffer))
        buffer[:len(raw)] = raw
        return len(raw)
