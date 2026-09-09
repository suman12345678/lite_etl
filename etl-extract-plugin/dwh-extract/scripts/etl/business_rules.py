"""Tiny, extensible row-level business-rule engine.

A rule in sources.json is a string: "name" or "name:arg".
Each rule is a function (rows, arg) -> (kept_rows, rejected_rows).
Add one by writing a function and decorating it with @rule("name").
Rejected rows get a "_reject_reason" key and are written to rejects.csv.
"""
from __future__ import annotations

_RULES: dict = {}


def rule(name: str):
    def deco(fn):
        _RULES[name] = fn
        return fn
    return deco


def available() -> list[str]:
    return sorted(_RULES)


@rule("trim_whitespace")
def _trim(rows, arg):
    for r in rows:
        for k, v in list(r.items()):
            if isinstance(v, str):
                r[k] = v.strip()
    return rows, []


@rule("rename")
def _rename(rows, arg):
    """arg: 'old->new'"""
    old, new = (p.strip() for p in arg.split("->", 1))
    for r in rows:
        if old in r:
            r[new] = r.pop(old)
    return rows, []


@rule("upper")
def _upper(rows, arg):
    for r in rows:
        if isinstance(r.get(arg), str):
            r[arg] = r[arg].upper()
    return rows, []


@rule("lower")
def _lower(rows, arg):
    for r in rows:
        if isinstance(r.get(arg), str):
            r[arg] = r[arg].lower()
    return rows, []


@rule("mask")
def _mask(rows, arg):
    """Light PII masking for a column (keeps first char + email domain)."""
    for r in rows:
        v = r.get(arg)
        if isinstance(v, str) and v:
            if "@" in v:
                local, _, domain = v.partition("@")
                r[arg] = f"{local[:1]}***@{domain}"
            else:
                r[arg] = f"{v[:1]}***"
    return rows, []


@rule("cast_int")
def _cast_int(rows, arg):
    kept, rejected = [], []
    for r in rows:
        try:
            r[arg] = int(float(r[arg]))
            kept.append(r)
        except (KeyError, TypeError, ValueError):
            r["_reject_reason"] = f"cast_int failed for '{arg}' (value={r.get(arg)!r})"
            rejected.append(r)
    return kept, rejected


@rule("drop_if_null")
def _drop_if_null(rows, arg):
    kept, rejected = [], []
    for r in rows:
        v = r.get(arg)
        if v is None or (isinstance(v, str) and v.strip() == ""):
            r["_reject_reason"] = f"null/empty '{arg}'"
            rejected.append(r)
        else:
            kept.append(r)
    return kept, rejected


def apply_rules(rows, rule_specs):
    """Run each rule in order. Returns (kept_rows, all_rejected, applied_specs)."""
    rejected_all: list = []
    applied: list = []
    for spec in rule_specs:
        name, _, arg = spec.partition(":")
        name, arg = name.strip(), arg.strip()
        if name not in _RULES:
            raise ValueError(f"Unknown business rule '{name}'. Available: {available()}")
        rows, rejected = _RULES[name](rows, arg)
        rejected_all.extend(rejected)
        applied.append(spec)
    return rows, rejected_all, applied
