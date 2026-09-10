{% macro surrogate_key(cols) %}
  {# wrap so the hash impl stays swappable (portability stance, transformation-design s.8) #}
  {{ return(dbt_utils.generate_surrogate_key(cols)) }}
{% endmacro %}
