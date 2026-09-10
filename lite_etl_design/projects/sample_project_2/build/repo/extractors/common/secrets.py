"""secret-scope:// resolver + PII hashing. Buildsheet: component-buildsheet-secrets.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
import hashlib


class SecretNotFound(Exception):
    ...


class SubjectErased(Exception):
    ...


def resolve(ref: str) -> str:
    """ref = secret-scope://northwind/<env>/<system>#<field>. Backend via NW_SECRETS_BACKEND."""
    raise NotImplementedError  # TODO env | databricks backend; never log the value


def resolve_mapping(system: str, fields: list[str]) -> dict[str, str]:
    raise NotImplementedError  # TODO


def hash_pii(value: str, salt: str) -> str:
    return hashlib.sha256((salt + value.strip().lower()).encode()).hexdigest()


def subject_salt(customer_bk: str) -> str:
    raise NotImplementedError  # TODO _state.pii_salts lookup; missing -> SubjectErased

