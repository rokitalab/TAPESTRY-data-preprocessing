#!/usr/bin/env python3
"""
03_tesj_cpm.py

ETL for TESJ CPM matrices → tesj_cpm table.
Loads both tumor and control RDS files and unpivots junction × sample → rows.
Log2 batch-corrected CPM (tumor only) is merged in before insertion.

Run:
  python -m pipelines.03_tesj_cpm

Environment (read by db package):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import pandas as pd

from db.connection import get_connection

TUMOR_FILE = Path("data/v2/tumor-enriched-oncofetal-splice-junction-cpm.rds")
CTRLS_FILE = Path("data/v2/tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds")
LOG2_FILE  = Path("data/v2/tumor-enriched-oncofetal-splice-junction-log2-cpm-combat-corrected.qs2")

_BATCH = 50_000


def _read_rds(path: Path) -> pd.DataFrame:
    r_code = f"write.table(readRDS('{path}'), stdout(), sep='\\t', row.names=FALSE, quote=FALSE)"
    result = subprocess.run(
        ["Rscript", "--vanilla", "-e", r_code],
        capture_output=True, text=True, check=True,
    )
    return pd.read_csv(io.StringIO(result.stdout), sep="\t")


def _read_qs2(path: Path) -> pd.DataFrame:
    r_code = f"library(qs2); write.table(qs_read('{path}'), stdout(), sep='\\t', row.names=FALSE, quote=FALSE)"
    result = subprocess.run(
        ["Rscript", "--vanilla", "-e", r_code],
        capture_output=True, text=True, check=True,
    )
    return pd.read_csv(io.StringIO(result.stdout), sep="\t")


def _insert(cur, rows: list[tuple]) -> None:
    cur.executemany(
        """
        INSERT INTO tesj_cpm (junction, biospecimen_id, cpm, log2_cpm_corrected)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (junction, biospecimen_id) DO NOTHING
        """,
        rows,
    )


def _to_long(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    return df.melt(id_vars="junction", var_name="biospecimen_id", value_name=value_name)


def _nullable(val) -> float | None:
    return None if pd.isna(val) else float(val)


def load_tumor(conn) -> None:
    print(f"Reading tumor CPM ({TUMOR_FILE.name})...")
    cpm = _to_long(_read_rds(TUMOR_FILE), "cpm")

    print(f"Reading log2 corrected CPM ({LOG2_FILE.name})...")
    log2 = _to_long(_read_qs2(LOG2_FILE), "log2_cpm_corrected")

    merged = cpm.merge(log2, on=["junction", "biospecimen_id"], how="left")
    print(f"  {len(merged):,} rows ({merged['log2_cpm_corrected'].isna().sum():,} NULL log2)")

    tuples = [
        (j, b, _nullable(c), _nullable(l))
        for j, b, c, l in merged.itertuples(index=False, name=None)
    ]
    print(f"  Inserting {len(tuples):,} rows in batches of {_BATCH:,}...")

    with conn.cursor() as cur:
        for start in range(0, len(tuples), _BATCH):
            _insert(cur, tuples[start : start + _BATCH])

    conn.commit()
    print(f"  Done.")


def load_controls(conn) -> None:
    print(f"Reading controls ({CTRLS_FILE.name})...")
    df = _read_rds(CTRLS_FILE)
    long = _to_long(df, "cpm")
    print(f"  {len(long):,} rows")

    tuples = [
        (j, b, _nullable(c), None)
        for j, b, c in long.itertuples(index=False, name=None)
    ]
    print(f"  Inserting {len(tuples):,} rows in batches of {_BATCH:,}...")

    with conn.cursor() as cur:
        for start in range(0, len(tuples), _BATCH):
            _insert(cur, tuples[start : start + _BATCH])

    conn.commit()
    print(f"  Done.")


def main() -> None:
    for path in (TUMOR_FILE, CTRLS_FILE, LOG2_FILE):
        if not path.exists():
            raise SystemExit(f"Input file not found: {path}")

    with get_connection() as conn:
        load_tumor(conn)
        load_controls(conn)

    print("03_tesj_cpm done.")


if __name__ == "__main__":
    main()
