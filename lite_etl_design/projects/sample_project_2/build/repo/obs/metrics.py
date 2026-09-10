"""emit(name, value, **dims); backends stdout|statsd|otlp. Buildsheet: component-buildsheet-observability.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from contextlib import contextmanager


def emit(name: str, value: float, **dims) -> None:
    raise NotImplementedError  # TODO dispatch on obs.metrics_backend


@contextmanager
def timer(name: str, **dims):
    raise NotImplementedError  # TODO emit run_duration_s
    yield

