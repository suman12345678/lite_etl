"""Config loading. One JSON file (config/sources.json) describes the landing
zone and every source. No third-party deps, so no YAML.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_ENV = "ETL_CONFIG"
LANDING_ENV = "ETL_LANDING_ZONE"


def plugin_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    # scripts/etl/config.py -> plugin root is three levels up
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    env = os.environ.get(CONFIG_ENV)
    return Path(env) if env else plugin_root() / "config" / "sources.json"


def _expand(value: str) -> str:
    return os.path.expanduser(os.path.expandvars(value))


class Source:
    def __init__(self, raw: dict, base_dir: Path):
        self.raw = raw
        self.base_dir = base_dir
        self.name: str = raw["name"]
        self.type: str = raw["type"]
        self.enabled: bool = raw.get("enabled", True)
        self.connection: dict = raw.get("connection", {})
        self.extract: dict = raw.get("extract", {"mode": "full"})
        self.business_rules: list[str] = raw.get("business_rules", [])
        self.reconciliation: dict = raw.get("reconciliation", {})

    def resolve_path(self, value: str) -> Path:
        p = Path(_expand(value))
        return p if p.is_absolute() else (self.base_dir / p).resolve()

    def __repr__(self) -> str:
        return f"<Source {self.name} ({self.type}){'' if self.enabled else ' disabled'}>"


class Config:
    def __init__(self, path: Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Config not found: {self.path}")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.base_dir = self.path.parent

        raw_lz = os.environ.get(LANDING_ENV) or data.get("landing_zone")
        if raw_lz:
            lz = Path(_expand(raw_lz))
            self.landing_zone = lz if lz.is_absolute() else (self.base_dir / lz).resolve()
        else:
            self.landing_zone = plugin_root() / "landing"

        self.sources = [Source(s, self.base_dir) for s in data.get("sources", [])]

    def get(self, name: str) -> Source:
        for s in self.sources:
            if s.name == name:
                return s
        known = [s.name for s in self.sources]
        raise KeyError(f"No source named '{name}'. Known sources: {known}")


def load_config(path: str | os.PathLike | None = None) -> Config:
    return Config(Path(path) if path else default_config_path())
