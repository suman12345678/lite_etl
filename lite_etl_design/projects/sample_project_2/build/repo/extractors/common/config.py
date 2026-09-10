"""Config loader: defaults -> <env>.yml -> <env>.generated.yml -> env vars. Buildsheet: component-buildsheet-config.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass


class ConfigError(Exception):
    ...


@dataclass(frozen=True)
class Settings:
    env: str
    catalog: str
    # TODO: storage.*, sources.*, dq.*, recon.*, secrets.*, lineage.* (see buildsheet)


def load_settings(env: str, generated_path: str | None = None) -> Settings:
    """Merge the YAML layers, apply NW_* env overrides, validate, freeze."""
    raise NotImplementedError  # TODO

