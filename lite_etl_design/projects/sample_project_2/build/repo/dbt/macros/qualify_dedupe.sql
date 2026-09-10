{% macro qualify_dedupe(partition_by, order_by) %}
  -- TODO QUALIFY row_number() over (...) = 1 ; DuckDB fallback for --target ci
{% endmacro %}
