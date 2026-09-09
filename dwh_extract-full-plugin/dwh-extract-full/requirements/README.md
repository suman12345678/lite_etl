# requirements/ — where you tell the plugin what to extract

This folder is the **input tray**. You describe a data source here (in whatever
form you have it), and the plugin turns that description into runnable
configuration under `../config/`.

## Folders

| Folder | What goes here |
|--------|----------------|
| `inbox/` | **Drop your files here.** Any format: the filled-in templates below, a Word/Excel mapping doc, a PDF spec, a CSV data dictionary, an exported email thread, a Confluence page saved as Markdown. One source per file is cleanest, but a bundle is fine. |
| `templates/` | Blank templates to fill in. Not required — they just make the intake unambiguous. Copy one, fill it, save it into `inbox/`. |
| `examples/` | A worked example (`customers-intake.md`) showing a completed intake. |
| `processed/` | Where an intake file is moved **after** its config has been generated and you've reviewed it. Keeps `inbox/` = "not yet done". |

## Templates provided

- `source-intake.md` — the core "what is this source" questionnaire
- `field-mapping.csv` — source field → target field, type, PII class, transform
- `data-quality-rules.md` — the business-rule checks to apply during extraction
- `reconciliation-spec.md` — how a run is proven correct before publish
- `sla-and-schedule.md` — cadence, deadlines, dependencies, retries, escalation
- `security-classification.md` — classification, masking policy, secret location

You don't have to use all of them. `source-intake.md` + `field-mapping.csv` is
enough to get a first extraction running.

## How to use it

1. **Add your file** to `requirements/inbox/` (copy a template and fill it, or
   just drop the spec you already have).
2. **Generate draft config** — either:
   - run `/ingest-requirements` (Claude Code command), or
   - ask the **`requirements-analyst`** agent: *"process the new file in
     requirements/inbox"*.
3. The analyst writes drafts into `../config/`:
   - `config/connections/<name>.connection.yaml` (if a new connection is needed)
   - `config/sources/<name>.source.yaml`
   - `config/business_rules/<name>.ruleset.yaml`
   - `config/reconciliation/<name>.recon.yaml`
   - `config/data_contracts/<name>.contract.yaml`
   …plus a list of **open questions / gaps** it couldn't infer.
4. **Review and edit** the drafts. Put real secret *references* (not values) in
   the connection file — see `../config/secrets/README.md`.
5. **Validate**: `/validate-config`.
6. **First run**: `/extract <name>` → check `/dq-report <name>` and
   `/reconcile <name>`.
7. **Move the intake file** to `requirements/processed/`.

## Secrets

Never put passwords, keys, or tokens in these files or in `config/`. Use a
reference the engine resolves at run time: `env://VAR`, `file://path`,
`vault://secret/path#field`, `awssm://name`, `gcpsm://name`, `azkv://vault/name`.
See `../config/secrets/README.md`.

> **SCAFFOLD note:** `/ingest-requirements` and the `requirements-analyst` agent
> are stubs right now. The folder contract above is stable — the logic behind it
> is filled in later.
