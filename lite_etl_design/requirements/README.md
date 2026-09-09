# requirements/ (harness) - Phase 1 inputs that are shared across all projects

This folder holds the **reusable** Phase 1 material. It is part of the harness,
not part of any one project.

| Item | Purpose |
|------|---------|
| `question-bank.md` | The coverage checklist the interviewer works through - project brief, sources, targets & loading, transformations, data quality, reconciliation, lineage & governance, scheduling & orchestration, security & compliance, non-functional, and platform / transformation framework / deployment (target engine & portability, dbt, Terraform / IaC, CI/CD). Read it if you want to prepare answers in advance. |
| `templates/` | Blank per-area templates (`00`..`10` + `99`). The `gather-etl-requirements` skill copies these into a project's `requirements/` folder and fills them from the interview. You don't edit them directly. |

## Where the filled-in files go

Not here. Each project has its **own** workspace:

```
<workspace>/intake/          <- you drop existing docs here
<workspace>/requirements/    <- the finished 00..10 + README + 99-open-questions land here
```

The workspace is created by `/etl-new-project <name>` and can be a subfolder
(`projects/<name>/`) or any folder on disk. See `../MAP.md`.

## Rule about secrets

Never put a password, key, or token in `intake/` or the requirement files.
Describe the *location* only: "env var `BILLING_DB_PW`", "Vault path
`secret/etl/billing_ro`".
