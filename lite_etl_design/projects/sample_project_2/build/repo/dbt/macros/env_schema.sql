{% macro env_schema(base) %}
  -- TODO prefix/route schema per target (gold vs gold_pii, env isolation) (requirements/10)
  {{ base }}
{% endmacro %}
