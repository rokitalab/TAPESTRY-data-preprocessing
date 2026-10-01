#!/usr/bin/env python3
"""
sj_library_size.py

Computes per-sample library size (total unique_reads across every junction
row) from the raw merged splice-junction file (data/v3/SJ.merged.tsv.gz),
used as the CPM denominator by pipelines/05_gene_junction_summary.py.

No QC file in this release covers every sample's total mapped reads, so the
denominator is derived directly from the data instead. This is a single
~35-40 minute streaming pass over the full file; its output is cached to a
flat file so 05_gene_junction_summary.py (and any re-runs of it) don't have
to repeat the scan.

Run:
  python -m pipelines.sj_library_size
"""
from __future__ import annotations

import subprocess
from collections import defaultdict
from pathlib import Path

SJ_FILE = Path("data/v3/SJ.merged.tsv.gz")
OUTPUT_FILE = Path("data/v3/library_sizes.tsv")

_PROGRESS_EVERY = 200_000_000


def _open_sj():
    """Stream-decompress via the system gzip binary. Python's gzip module
    is ~4x slower than this for a file this size (measured)."""
    proc = subprocess.Popen(["gzcat", str(SJ_FILE)], stdout=subprocess.PIPE)
    return proc, proc.stdout


def compute_library_sizes() -> dict[str, int]:
    print("Computing per-sample library size (total unique_reads)...")
    sizes: dict[str, int] = defaultdict(int)
    proc, stream = _open_sj()
    next(stream)  # header
    n = 0
    for line in stream:
        parts = line.split(b"\t")
        sizes[parts[0].decode()] += int(parts[7])
        n += 1
        if n % _PROGRESS_EVERY == 0:
            print(f"  {n:,} rows...")
    proc.wait()
    print(f"  Done: {n:,} rows, {len(sizes):,} samples.")
    return dict(sizes)


def write_library_sizes(sizes: dict[str, int]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w") as f:
        f.write("sample_id\ttotal_unique_reads\n")
        for sample_id, total in sizes.items():
            f.write(f"{sample_id}\t{total}\n")
    print(f"Wrote {len(sizes):,} rows to {OUTPUT_FILE}")


def main() -> None:
    if not SJ_FILE.exists():
        raise SystemExit(f"Input file not found: {SJ_FILE}")

    sizes = compute_library_sizes()
    write_library_sizes(sizes)
    print("sj_library_size done.")


if __name__ == "__main__":
    main()
