"""Base class every source connector implements."""
from __future__ import annotations

import abc


class Extractor(abc.ABC):
    """A connector that pulls rows from one source system.

    Subclasses implement extract(). Config comes from self.source.connection
    (a dict from sources.json). Keep credentials OUT of that dict - read them
    from environment variables or a secret manager inside extract().
    """

    type_name = "base"

    def __init__(self, source):
        self.source = source

    @abc.abstractmethod
    def extract(self) -> list[dict]:
        """Return the source rows as a list of {column: value} dicts."""

    def describe(self) -> str:
        return f"{self.type_name}:{self.source.name}"
