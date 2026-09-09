"""Connector registry. Add a new source type in three lines:

    from .bigquery_source import BigQueryExtractor
    register("bigquery", BigQueryExtractor)

See bigquery_source.py.example and azure_blob_source.py.example for templates.
"""
from __future__ import annotations

from .csv_source import CsvExtractor

_REGISTRY: dict[str, type] = {
    "csv": CsvExtractor,
}


def register(type_name: str, cls: type) -> None:
    _REGISTRY[type_name] = cls


def registered_types() -> list[str]:
    return sorted(_REGISTRY)


def get_extractor(source):
    try:
        cls = _REGISTRY[source.type]
    except KeyError:
        raise ValueError(
            f"Unknown source type '{source.type}'. Registered: {registered_types()}. "
            f"Implement a connector in scripts/etl/extractors/ and register() it."
        )
    return cls(source)
