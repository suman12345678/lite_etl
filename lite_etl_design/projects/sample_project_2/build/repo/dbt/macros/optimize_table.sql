{% macro optimize_table() %}
  {# Databricks only; called from a weekly maintenance job, NOT per run (requirements/09 cost) #}
  {% if target.type == 'databricks' %}
    -- TODO: OPTIMIZE {{ this }} ZORDER BY (...)
  {% endif %}
{% endmacro %}
