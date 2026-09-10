"""Shared pytest fixtures. TODO: load tests/fixtures/<src>/sample.* into a DuckDB
file as bronze.<src>__<obj> for `make dbt-ci`, and build Settings/ReconResult helpers."""
import pytest


@pytest.fixture
def settings(tmp_path):
    raise NotImplementedError  # TODO load_settings("ci") pointed at tmp_path
