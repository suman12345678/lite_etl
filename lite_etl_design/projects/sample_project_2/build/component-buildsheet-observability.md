# Component buildsheet: `observability` (metrics + logging hooks)

- **Design refs:** `design/component-design.md#observability`,
  `design/architecture-overview.md` §4, `requirements/09` (observability),
  `requirements/07` (alerting). Full wiring is Phase 5
  (`hardening/observability-wiring.md`); Phase 3 builds the emit points.
- **Language / framework:** Python 3.12; `structlog` for JSON logs; a metrics
  seam (StatsD / OTLP / stdout in tests)
- **Repo path:** `build/repo/obs/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/obs/__init__.py` | |
| `build/repo/obs/log.py` | configure structlog: every line carries `run_id`, `pipeline`, `business_date`, `component` |
| `build/repo/obs/metrics.py` | `emit(name, value, **dims)`; backends: `stdout` (tests), `statsd`, `otlp` |
| `build/repo/tests/unit/test_observability.py` | |

## Public interface

- **`bind(run_id, pipeline, business_date, component) -> Logger`** - returns a
  bound structlog logger; context propagates to child calls.
- **`metrics.emit(name: str, value: float, **dims)`** - the metric set from
  `component-design.md` / `09`: `rows_in`, `rows_out`, `bytes_landed`,
  `run_duration_s`, `freshness_lag_s`, `reject_rate`, `recon_delta`,
  `compute_spend`, `gate_result`.
- **`metrics.timer(name, **dims)`** - context manager -> emits `run_duration_s`.

## Config keys

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `obs.metrics_backend` | str | `stdout` | `stdout` \| `statsd` \| `otlp` |
| `obs.log_level` | str | `INFO` | |
| `obs.statsd_addr` / `obs.otlp_endpoint` | str | - | when backend set |

## Key logic

1. `log.py`: JSON renderer, ISO timestamps, `run_id` etc. as top-level keys;
   secret-looking values scrubbed by a processor.
2. `metrics.py`: dispatch on backend; `stdout` backend appends a line the tests
   assert on.

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| bound context | `bind(...)` then `.info("x")` | log record has all 4 context keys |
| metric emit (stdout) | `emit("rows_in", 10, source="oltp")` | one line with name/value/dims |
| timer | `with metrics.timer("run_duration_s", ...)` | emits a positive duration |
| secret scrub | log a dict containing `password=...` | value replaced with `***` |
| backend switch | `obs.metrics_backend=statsd` + mock socket | packet formatted correctly |

## Fixtures needed

None (captured stdout / caplog / mock socket).

## Done checklist

- [ ] files created  - [ ] every metric in `09` has an `emit` call site in the
      other components (grep check)
- [ ] logs are JSON with the 4 context keys  - [ ] secrets scrubbed
- [ ] wired into `make test`
