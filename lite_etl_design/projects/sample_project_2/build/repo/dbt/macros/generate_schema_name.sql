{#
  Schema routing. On the `ci` (DuckDB) target we want the raw folder schema names
  (silver / gold / gold_pii) so local objects read like production. On warehouse
  targets keep dbt's default `<target.schema>_<custom>` namespacing per env.
  ref: pipeline/environments-and-config.md, requirements/10
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'ci' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
