{#
  Convert `amount` (in `currency`) to USD using dim_fx_rate. Carry-forward aware:
  if `date_col` is given, take the latest rate on or before that date; otherwise
  the single current rate. Engine-specific SQL stays confined to this macro
  (portability stance, transformation-design.md s.8 / ADR-003).
#}
{% macro to_usd(amount, currency, date_col=none) -%}
    round({{ amount }} / nullif((
        select r.rate_per_usd
        from {{ ref('dim_fx_rate') }} r
        where r.currency = {{ currency }}
        {%- if date_col %}
          and r.rate_date <= {{ date_col }}
          order by r.rate_date desc
          limit 1
        {%- endif %}
    ), 0), 2)
{%- endmacro %}
