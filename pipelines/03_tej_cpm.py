#!/usr/bin/env python3
"""
03_tej_cpm.py

ETL for TEJ CPM matrices → tej_cpm table.
Loads tumor (qs2) and control (RDS) CPM files and unpivots junction × sample → rows.
ComBat batch-corrected CPM (tumor only; linear scale, not log2) is merged in
before insertion.

Rows are bulk-loaded with COPY in junction chunks, so the full long-format
table (~97M rows) is never held in memory. tej_cpm's primary key, foreign keys
and index are added after the load (building them once is far faster than
maintaining them row by row), so the table must be empty before this runs.
Everything happens in one transaction: a failure leaves tej_cpm empty.

Run:
  python -m pipelines.03_tej_cpm

Environment (read by db package):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from db.connection import get_connection

TUMOR_FILE = Path("data/tumor-enriched-oncofetal-splice-junction-cpm.qs2")
CTRLS_FILE = Path("data/tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds")
CORRECTED_FILE = Path("data/tumor-enriched-oncofetal-splice-junction-cpm-combat-corrected.qs2")

# Junctions per COPY chunk; ~2M rows per chunk at ~2,000 samples.
_CHUNK = 1_000

# Constraints/indexes are dropped (if a previous migration created them) before
# the load and re-created after it.
_DROP_CONSTRAINTS = """
    ALTER TABLE tej_cpm DROP CONSTRAINT IF EXISTS tej_cpm_pkey;
    ALTER TABLE tej_cpm DROP CONSTRAINT IF EXISTS tej_cpm_junction_fkey;
    ALTER TABLE tej_cpm DROP CONSTRAINT IF EXISTS tej_cpm_biospecimen_id_fkey;
    DROP INDEX IF EXISTS tej_cpm_biospecimen_id_idx;
"""
_ADD_CONSTRAINTS = """
    ALTER TABLE tej_cpm ADD CONSTRAINT tej_cpm_pkey PRIMARY KEY (junction, biospecimen_id);
    ALTER TABLE tej_cpm ADD CONSTRAINT tej_cpm_junction_fkey
        FOREIGN KEY (junction) REFERENCES tej (junction) ON DELETE CASCADE;
    ALTER TABLE tej_cpm ADD CONSTRAINT tej_cpm_biospecimen_id_fkey
        FOREIGN KEY (biospecimen_id) REFERENCES sample (biospecimen_id) ON DELETE CASCADE;
    CREATE INDEX tej_cpm_biospecimen_id_idx ON tej_cpm (biospecimen_id);
"""


def _read_r(r_expr: str) -> pd.DataFrame:
    """Run an R expression yielding a junction × sample table and read it as a DataFrame.

    R's output is streamed straight into pandas rather than buffered as one string.
    """
    r_code = f"write.table({r_expr}, stdout(), sep='\\t', row.names=FALSE, quote=FALSE)"
    proc = subprocess.Popen(
        ["Rscript", "--vanilla", "-e", r_code],
        stdout=subprocess.PIPE, text=True,
    )
    df = pd.read_csv(proc.stdout, sep="\t")
    if proc.wait() != 0:
        raise RuntimeError(f"Rscript failed ({proc.returncode}) reading: {r_expr}")
    return df


def _read_rds(path: Path) -> pd.DataFrame:
    return _read_r(f"readRDS('{path}')")


def _read_qs2(path: Path) -> pd.DataFrame:
    return _read_r(f"qs2::qs_read('{path}')")


def _copy_matrix(cur, cpm: pd.DataFrame, corrected: pd.DataFrame | None) -> int:
    """COPY a wide junction × sample CPM matrix into tej_cpm, _CHUNK junctions at a time.

    `corrected`, if given, is a matrix with the same junctions and samples; its
    values go to cpm_corrected (NULL where it has no value, or when it is None).
    """
    samples = cpm.columns.drop("junction")
    junctions = cpm["junction"].to_numpy()
    cpm_vals = cpm[samples].to_numpy(dtype=float)
    if corrected is not None:
        corrected_vals = (
            corrected.set_index("junction")
            .reindex(index=junctions, columns=samples)
            .to_numpy(dtype=float)
        )

    n_samples = len(samples)
    n_rows = 0
    with cur.copy(
        "COPY tej_cpm (junction, biospecimen_id, cpm, cpm_corrected) FROM STDIN"
    ) as copy:
        for start in range(0, len(junctions), _CHUNK):
            end = min(start + _CHUNK, len(junctions))
            block = pd.DataFrame({
                "junction": np.repeat(junctions[start:end], n_samples),
                "biospecimen_id": np.tile(samples, end - start),
                "cpm": cpm_vals[start:end].ravel(),
                "cpm_corrected": (
                    corrected_vals[start:end].ravel()
                    if corrected is not None else np.nan
                ),
            })
            buf = io.StringIO()
            block.to_csv(buf, sep="\t", header=False, index=False, na_rep="\\N")
            copy.write(buf.getvalue())
            n_rows += len(block)
            print(f"    {end:,}/{len(junctions):,} junctions ({n_rows:,} rows)", end="\r")
    print()
    return n_rows


def load_tumor(cur) -> None:
    print(f"Reading tumor CPM ({TUMOR_FILE.name})...")
    cpm = _read_qs2(TUMOR_FILE)

    print(f"Reading batch-corrected CPM ({CORRECTED_FILE.name})...")
    corrected = _read_qs2(CORRECTED_FILE)

    print(f"  COPYing {len(cpm):,} junctions × {len(cpm.columns) - 1:,} samples...")
    n = _copy_matrix(cur, cpm, corrected)
    print(f"  {n:,} tumor rows loaded.")


def load_controls(cur) -> None:
    print(f"Reading controls ({CTRLS_FILE.name})...")
    cpm = _read_rds(CTRLS_FILE)

    print(f"  COPYing {len(cpm):,} junctions × {len(cpm.columns) - 1:,} samples...")
    n = _copy_matrix(cur, cpm, None)
    print(f"  {n:,} control rows loaded.")


def main() -> None:
    for path in (TUMOR_FILE, CTRLS_FILE, CORRECTED_FILE):
        if not path.exists():
            raise SystemExit(f"Input file not found: {path}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT EXISTS (SELECT 1 FROM tej_cpm)")
            if cur.fetchone()[0]:
                raise SystemExit(
                    "tej_cpm is not empty -- TRUNCATE or drop it before reloading."
                )

            cur.execute(_DROP_CONSTRAINTS)
            load_tumor(cur)
            load_controls(cur)

            print("Adding primary key, foreign keys and index...")
            cur.execute(_ADD_CONSTRAINTS)
            cur.execute("ANALYZE tej_cpm")
        conn.commit()

    print("03_tej_cpm done.")


if __name__ == "__main__":
    main()
