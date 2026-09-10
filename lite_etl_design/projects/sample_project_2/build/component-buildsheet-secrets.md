# Component buildsheet: `secrets` (reference resolver + PII hashing)

- **Design refs:** `design/component-design.md#secrets--security`,
  `requirements/08` (secret management, PII treatment, crypto-shred RTBF)
- **Language / framework:** Python 3.12; `hashlib`; a pluggable backend
  (Databricks secret scope in prod, env vars locally)
- **Repo path:** `build/repo/extractors/common/secrets.py`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/extractors/common/secrets.py` | resolve `secret-scope://…#field` refs; provide the PII hashing helper |
| `build/repo/tests/unit/test_secrets.py` | |

## Public interface

- **`resolve(ref: str) -> str`** - `ref` is `secret-scope://northwind/<env>/<system>#<field>`.
  Backend chosen by `NW_SECRETS_BACKEND` (`env` | `databricks`). `env` backend
  maps the ref to an env var `NW_SECRET__<SYSTEM>__<FIELD>`.
- **`resolve_mapping(system: str, fields: list[str]) -> dict[str,str]`**
- **`hash_pii(value: str, salt: str) -> str`** - `sha256((salt + value.strip().lower()).encode()).hexdigest()`;
  returns 64 lowercase hex. Used by the `int_customer__*` dbt models via a UDF
  seam and by any Python that must pre-hash.
- **`subject_salt(customer_bk: str) -> str`** - per-subject salt lookup (for
  crypto-shred RTBF: deleting the salt makes the hash unrecoverable).

## Config keys

| Key | Type | Default | Required | Notes |
|-----|------|---------|----------|-------|
| `NW_SECRETS_BACKEND` | env | `env` | no | `env` locally, `databricks` in the pipeline |
| `secrets.scope_prefix` | str | `northwind/<env>` | yes | from `config` |
| `secrets.pii_salt_ref` | str | `secret-scope://northwind/<env>/pii#salt` | yes | global salt; per-subject salts layered on top |

## Key logic

1. Parse the ref (`urllib.parse`), split `#field`.
2. Dispatch to the backend; cache within a process (never log the value).
3. `hash_pii`: normalise (`strip().lower()`), prepend salt, sha256, hexdigest.
4. `subject_salt`: read from `_state.pii_salts` (Delta) keyed by `customer_bk`;
   missing salt for an erased subject => raise `SubjectErased`.

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| resolve env backend | monkeypatch `NW_SECRET__OLTP__PASSWORD=x` | `resolve("secret-scope://…/oltp#password") == "x"` |
| missing secret | no env var | raises `SecretNotFound` naming the ref, no value in the message |
| hash determinism | fixed salt + email | stable 64-hex; `^[a-f0-9]{64}$` |
| hash normalisation | ` Foo@BAR.com ` vs `foo@bar.com` | same hash |
| value never logged | caplog | no secret value in any log record |
| erased subject | salt row absent | `subject_salt` raises `SubjectErased` |

## Fixtures needed

None beyond monkeypatched env vars and a tmp state dir.

## Done checklist

- [ ] files created  - [ ] interface matches  - [ ] all tests pass
- [ ] no secret value ever logged or returned in an error  - [ ] wired into `make test`
