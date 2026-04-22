#!/usr/bin/env python3
"""
03_tesj_cpm.py

ETL for TESJ CPM matrices → tesj_cpm table.
Loads both tumor and control RDS files and unpivots junction × sample → rows.

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

_BATCH = 50_000


def _read_rds(path: Path) -> pd.DataFrame:
    r_code = f"write.table(readRDS('{path}'), stdout(), sep='\\t', row.names=FALSE, quote=FALSE)"
    result = subprocess.run(
        ["Rscript", "--vanilla", "-e", r_code],
        capture_output=True, text=True, check=True,
    )
    return pd.read_csv(io.StringIO(result.stdout), sep="\t")


def _insert(cur, rows: list[tuple]) -> None:
    cur.executemany(
        """
        INSERT INTO tesj_cpm (junction, biospecimen_id, cpm)
        VALUES (%s, %s, %s)
        ON CONFLICT (junction, biospecimen_id) DO NOTHING
        """,
        rows,
    )


def load(conn, path: Path, label: str) -> None:
    print(f"Reading {label} ({path.name})...")
    df = _read_rds(path)

    sample_cols = [c for c in df.columns if c != "junction"]
    total_rows = len(df) * len(sample_cols)
    print(f"  {len(df):,} junctions × {len(sample_cols):,} samples = {total_rows:,} rows")

    long = df.melt(id_vars="junction", var_name="biospecimen_id", value_name="cpm")
    tuples = [
        (j, b, None if pd.isna(c) else float(c))
        for j, b, c in long.itertuples(index=False, name=None)
    ]
    print(f"  Inserting {len(tuples):,} rows in batches of {_BATCH:,}...")

    inserted = 0
    with conn.cursor() as cur:
        for start in range(0, len(tuples), _BATCH):
            _insert(cur, tuples[start : start + _BATCH])
            inserted += min(_BATCH, len(tuples) - start)

    conn.commit()
    print(f"  Inserted {inserted:,} rows.")


def main() -> None:
    for path in (TUMOR_FILE, CTRLS_FILE):
        if not path.exists():
            raise SystemExit(f"Input file not found: {path}")

    with get_connection() as conn:
        load(conn, TUMOR_FILE, "tumor")
        load(conn, CTRLS_FILE, "controls")

    print("03_tesj_cpm done.")


if __name__ == "__main__":
    main()
