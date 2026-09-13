{#
  One hashing expression, three warehouses. The kind of thin seam that lets the
  same models run on DuckDB, Databricks or Snowflake unchanged (Non-functional:
  billing_email -> sha256 at the staging boundary).
#}
{% macro to_sha256(col) -%}
    {{ return(adapter.dispatch('to_sha256', 'projectprod')(col)) }}
{%- endmacro %}

{% macro default__to_sha256(col) -%}
    sha256(cast({{ col }} as varchar))
{%- endmacro %}

{% macro duckdb__to_sha256(col) -%}
    sha256(cast({{ col }} as varchar))
{%- endmacro %}

{% macro snowflake__to_sha256(col) -%}
    sha2(cast({{ col }} as varchar), 256)
{%- endmacro %}

{% macro databricks__to_sha256(col) -%}
    sha2(cast({{ col }} as string), 256)
{%- endmacro %}
