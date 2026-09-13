"""The real "rules" + "publish" components from design.md: after `dbt build`
produces the marts, publish.gate runs rules.yml against them and either
publishes gold/ + _SUCCESS + advances the watermark, or blocks and exits 1.
demo/rules.py + demo/run.py are the SQLite-local equivalent of this module.
"""
