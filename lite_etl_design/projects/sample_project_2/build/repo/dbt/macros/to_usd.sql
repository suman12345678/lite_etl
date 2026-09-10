{% macro to_usd(amount, currency, date_col) %}
  -- TODO join dim_fx_rate at date_col, carry-forward aware (requirements/03)
  {{ amount }}
{% endmacro %}
