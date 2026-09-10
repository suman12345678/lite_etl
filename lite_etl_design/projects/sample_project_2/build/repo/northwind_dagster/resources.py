"""Resources for the northwind_daily code location - connections to Databricks,
S3, the secret resolver, dbt, and the alert routes. References only; no values.
Phase 4 scaffold - see pipeline/orchestration-wiring.md + environments-and-config.md.
"""

from __future__ import annotations

from dagster import ConfigurableResource, EnvVar


class SettingsResource(ConfigurableResource):
    """Layered config: defaults.yml <- <env>.yml <- <env>.generated.yml."""

    env: str = EnvVar("NORTHWIND_ENV")            # dev | stg | prd
    config_dir: str = "config"
    # TODO load + deep-merge in setup_for_execution; expose .catalog, .storage, .recon, ...


class DatabricksResource(ConfigurableResource):
    host: str = EnvVar("DATABRICKS_HOST")         # GitHub Environment secret / generated config
    token: str = EnvVar("DATABRICKS_TOKEN")
    http_path: str = ""                           # TODO config/<env>.generated.yml (warehouse.http_path)


class S3Resource(ConfigurableResource):
    region: str = EnvVar("AWS_REGION")
    # bucket URIs come from SettingsResource (storage.*_uri); no creds - task role / OIDC


class SecretResolverResource(ConfigurableResource):
    """Resolves secret-scope://northwind/<env>/<src>#<field> at runtime."""

    scope_prefix: str = ""                        # TODO from config (secrets.scope_prefix)


class DbtResource(ConfigurableResource):
    project_dir: str = "dbt"
    profiles_dir: str = "dbt/profiles"
    target: str = EnvVar("NORTHWIND_ENV")
    # curated_build uses this via dagster-dbt DbtCliResource in transform.py


class AlertResource(ConfigurableResource):
    pagerduty_routing_key: str = EnvVar("PAGERDUTY_ROUTING_KEY")   # page: SLA breach / reconcile FAIL / permanent error
    slack_webhook: str = EnvVar("SLACK_WEBHOOK")                   # #northwind-data: warnings, DQ digests, backfill
    # TODO: page(summary, links), warn(summary) helpers


RESOURCES = {
    "settings": SettingsResource(),
    "databricks": DatabricksResource(),
    "s3": S3Resource(),
    "secrets": SecretResolverResource(),
    "dbt": DbtResource(),
    "alerts": AlertResource(),
}
