"""Retrying HTTP client (429/5xx expo backoff, Retry-After). Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations


def request(method: str, url: str, *, retries: int = 3, **kw):
    """httpx request with expo backoff on 429/5xx and Retry-After honouring."""
    raise NotImplementedError  # TODO

