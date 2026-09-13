"""extract/ref -- ref.plans + ref.fx_rates, hand-maintained / daily CSVs on S3.

    python -m extract.ref              # both files, full refresh
    python -m extract.ref --only plans
    python -m extract.ref --only fx_rates

Bucket + keys come only from REF_S3_BUCKET / REF_PLANS_KEY / REF_FX_RATES_KEY (env
vars); AWS credentials come from the process's normal AWS credential chain (IAM
role in prod -- never a literal key here). Sources notes ref.fx_rates has weekend /
holiday gaps; those are landed as-is (a genuine gap in the source file) -- carry
forward happens in dbt (stg_ref__fx_rates + the fct_invoice FX join), not here.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from typing import Iterator

import boto3

from extract.common import RawSink, env, retry_call

PLAN_COLUMNS = ["plan_code", "monthly_price_usd", "plan_tier", "is_retired"]
FX_COLUMNS = ["rate_date", "currency", "rate_to_usd"]


def _s3():
    return boto3.client("s3", region_name=env("AWS_REGION", "us-east-1"))


def _read_csv(bucket: str, key: str) -> Iterator[dict]:
    client = _s3()

    def _do():
        return client.get_object(Bucket=bucket, Key=key)

    obj = retry_call(_do, max_attempts=4, base_delay_s=2.0)
    body = obj["Body"].read().decode("utf-8")
    yield from csv.DictReader(io.StringIO(body))


def fetch_plans() -> Iterator[tuple]:
    bucket = env("REF_S3_BUCKET")
    key = env("REF_PLANS_KEY", "ref/plans.csv")
    for r in _read_csv(bucket, key):
        yield (
            r["plan_code"],
            float(r["monthly_price_usd"]),
            r["plan_tier"],
            int(r.get("is_retired", 0) or 0),
        )


def fetch_fx_rates() -> Iterator[tuple]:
    bucket = env("REF_S3_BUCKET")
    key = env("REF_FX_RATES_KEY", "ref/fx_rates.csv")
    for r in _read_csv(bucket, key):
        yield (r["rate_date"], r["currency"].upper(), float(r["rate_to_usd"]))


def land_plans(sink: RawSink) -> int:
    return sink.replace_rows("ref_plans", PLAN_COLUMNS, list(fetch_plans()))


def land_fx_rates(sink: RawSink) -> int:
    return sink.replace_rows("ref_fx_rates", FX_COLUMNS, list(fetch_fx_rates()))


def run(only: str | None) -> None:
    sink = RawSink()
    try:
        if only in (None, "plans"):
            n = land_plans(sink)
            print(f"landed {n} ref.plans row(s) (full refresh)")
        if only in (None, "fx_rates"):
            n = land_fx_rates(sink)
            print(f"landed {n} ref.fx_rates row(s) (full refresh)")
    finally:
        sink.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", choices=["plans", "fx_rates"], default=None)
    args = ap.parse_args(argv)
    run(args.only)
    return 0


if __name__ == "__main__":
    sys.exit(main())
