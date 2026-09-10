"""Runnable local demo of the northwind_daily slice - see DEMO.md.

Plain DuckDB (no Databricks, no dbt, no Dagster, no cloud). Demonstrates:
  1. data load        -> synthetic fixtures land as bronze.*
  2. transform + DQ    -> bronze -> stg -> int -> dim/fct, with the
                          `gmv >= 0 unless is_return` rule quarantining bad rows
  3. reconciliation    -> row-count identity, GMV vs a control total, order == sum(lines);
                          PASS publishes to gold + writes _SUCCESS; FAIL blocks and exits 1
"""
