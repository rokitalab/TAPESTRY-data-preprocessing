#!/usr/bin/env python3
"""
05_gene_junction_summary.py

Loads the intermediate file produced by
pipelines/gene_junction_summary_compute.py (data/v3/gene_junction_summary.tsv)
into the gene_junction_summary table. plot_group names are resolved to
plot_group.id along the way (creating new lookup rows as needed) since the
TSV still carries the human-readable name -- gene_junction_summary_compute.py
has no DB connection to resolve ids itself.

The heavy lifting -- streaming the 23GB raw splice-junction file, attributing
each junction to its enclosing gene(s) and plot_group(s), and reducing to a
median CPM / total read count per key -- happens entirely in
gene_junction_summary_compute.py and needs no DB connection. This script is
the comparatively fast, DB-only tail end, kept separate so the expensive
compute pass never has to be repeated just to retry a load.

Run:
  python -m pipelines.gene_junction_summary_compute   # writes the TSV first
  python -m pipelines.05_gene_junction_summary         # then load it

Environment (read by db package):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""
from __future__ import annotations

from pathlib import Path

from db.connection import get_connection

INPUT_FILE = Path("data/v3/gene_junction_summary.tsv")

_BATCH = 50_000


def read_rows(path: Path):
    with path.open() as f:
        next(f)  # header
        for line in f:
            gene, chrom, istart, iend, strand, annotated, group, num_samples_detected, median_cpm, mean_cpm, total_reads = (
                line.rstrip("\n").split("\t")
            )
            yield (
                gene,
                chrom,
                int(istart),
                int(iend),
                strand or None,
                annotated == "1",
                group,
                int(num_samples_detected),
                float(median_cpm),
                float(mean_cpm),
                int(total_reads),
            )


def _group_id(cur, cache: dict[str, int], name: str) -> int:
    """plot_group has only a few dozen distinct values, so resolving them
    through `plot_group` (creating new rows as needed) costs at most a
    few dozen round trips for the whole load, not one per summary row."""
    if name in cache:
        return cache[name]
    cur.execute(
        """
        INSERT INTO plot_group (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    )
    group_id = cur.fetchone()[0]
    cache[name] = group_id
    return group_id


def load(conn, path: Path) -> None:
    batch: list[tuple] = []
    n = 0
    group_ids: dict[str, int] = {}
    with conn.cursor() as cur:
        for row in read_rows(path):
            gene, chrom, istart, iend, strand, annotated, group, num_samples_detected, median_cpm, mean_cpm, total_reads = row
            group_id = _group_id(cur, group_ids, group)
            batch.append((
                gene, chrom, istart, iend, strand, annotated, group_id,
                num_samples_detected, median_cpm, mean_cpm, total_reads,
            ))
            if len(batch) >= _BATCH:
                _insert(cur, batch)
                n += len(batch)
                batch.clear()
        if batch:
            _insert(cur, batch)
            n += len(batch)
    conn.commit()
    print(f"Loaded {n:,} rows into gene_junction_summary.")


def _insert(cur, batch: list[tuple]) -> None:
    cur.executemany(
        """
        INSERT INTO gene_junction_summary (
            gene_symbol, chr, intron_start, intron_end, strand, annotated,
            plot_group_id, num_samples_detected, median_cpm, mean_cpm, total_reads
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (gene_symbol, chr, intron_start, intron_end, strand, plot_group_id)
        DO UPDATE SET annotated = EXCLUDED.annotated,
                      num_samples_detected = EXCLUDED.num_samples_detected,
                      median_cpm = EXCLUDED.median_cpm,
                      mean_cpm = EXCLUDED.mean_cpm,
                      total_reads = EXCLUDED.total_reads
        """,
        batch,
    )


def main() -> None:
    if not INPUT_FILE.exists():
        raise SystemExit(
            f"Input file not found: {INPUT_FILE}\n"
            "Run `python -m pipelines.gene_junction_summary_compute` first."
        )

    with get_connection() as conn:
        load(conn, INPUT_FILE)

    print("05_gene_junction_summary done.")


if __name__ == "__main__":
    main()
