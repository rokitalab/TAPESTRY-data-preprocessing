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

This is a full reload: in one transaction the table is truncated, its primary
key, foreign key and indexes are dropped, the TSV is bulk-loaded with COPY, and
the constraints and indexes are rebuilt once at the end. A failure rolls back
to the previous contents. The table is locked against reads while it runs.

Run:
  python -m pipelines.gene_junction_summary_compute   # writes the TSV first
  python -m pipelines.05_gene_junction_summary         # then load it

Environment (read by db package):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""
from __future__ import annotations

import gzip
from pathlib import Path

from psycopg import sql

from db.connection import get_connection

INPUT_FILE = Path("data/v3/gene_junction_summary.tsv.gz")

# TSV lines per COPY write.
_BATCH = 100_000

_ADD_CONSTRAINTS = """
    ALTER TABLE gene_junction_summary ADD CONSTRAINT gene_junction_summary_pkey
        PRIMARY KEY (gene_symbol, chr, intron_start, intron_end, plot_group_id);
    ALTER TABLE gene_junction_summary ADD CONSTRAINT gene_junction_summary_plot_group_id_fkey
        FOREIGN KEY (plot_group_id) REFERENCES plot_group (id);
    CREATE INDEX gene_junction_summary_gene_symbol_idx ON gene_junction_summary (gene_symbol);
    CREATE INDEX gene_junction_summary_plot_group_id_idx ON gene_junction_summary (plot_group_id);
"""


def read_groups(path: Path) -> set[str]:
    """Distinct plot_group names in the TSV, so their ids can be resolved
    before COPY starts (no other statements can run mid-COPY)."""
    groups: set[str] = set()
    with gzip.open(path, "rt") as f:
        next(f)  # header
        for line in f:
            groups.add(line.split("\t", 7)[6])
    return groups


def _resolve_group_ids(cur, names: set[str]) -> dict[str, int]:
    """plot_group has only a few dozen distinct values, so this is at most a
    few dozen round trips for the whole load, not one per summary row."""
    ids: dict[str, int] = {}
    for name in sorted(names):
        cur.execute(
            """
            INSERT INTO plot_group (name) VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (name,),
        )
        ids[name] = cur.fetchone()[0]
    return ids


def copy_lines(path: Path, group_ids: dict[str, int]):
    """Yield TSV rows rewritten as COPY text-format lines: empty strand → NULL,
    annotated "1" → true, plot_group name → id. Numeric fields pass through
    as-is and are validated by Postgres."""
    with gzip.open(path, "rt") as f:
        next(f)  # header
        for line in f:
            gene, chrom, istart, iend, strand, annotated, group, num_samples_detected, median_cpm, mean_cpm, total_reads = (
                line.rstrip("\n").split("\t")
            )
            yield "\t".join((
                gene, chrom, istart, iend,
                strand or "\\N",
                "t" if annotated == "1" else "f",
                str(group_ids[group]),
                num_samples_detected, median_cpm, mean_cpm, total_reads,
            )) + "\n"


def _drop_constraints_and_indexes(cur) -> None:
    """Drop the PK, FK and every secondary index -- including any duplicate
    unnamed indexes left by earlier versions of the migration."""
    cur.execute("ALTER TABLE gene_junction_summary DROP CONSTRAINT IF EXISTS gene_junction_summary_pkey")
    cur.execute("ALTER TABLE gene_junction_summary DROP CONSTRAINT IF EXISTS gene_junction_summary_plot_group_id_fkey")
    cur.execute(
        """
        SELECT indexname FROM pg_indexes
        WHERE schemaname = current_schema() AND tablename = 'gene_junction_summary'
        """
    )
    for (name,) in cur.fetchall():
        cur.execute(sql.SQL("DROP INDEX {}").format(sql.Identifier(name)))


def load(conn, path: Path) -> None:
    print("Scanning plot_group names...")
    groups = read_groups(path)

    with conn.cursor() as cur:
        group_ids = _resolve_group_ids(cur, groups)
        print(f"  {len(group_ids)} plot_groups resolved.")

        cur.execute("TRUNCATE gene_junction_summary")
        _drop_constraints_and_indexes(cur)

        print("COPYing rows...")
        n = 0
        batch: list[str] = []
        with cur.copy(
            """
            COPY gene_junction_summary (
                gene_symbol, chr, intron_start, intron_end, strand, annotated,
                plot_group_id, num_samples_detected, median_cpm, mean_cpm, total_reads
            ) FROM STDIN
            """
        ) as copy:
            for line in copy_lines(path, group_ids):
                batch.append(line)
                if len(batch) >= _BATCH:
                    copy.write("".join(batch))
                    n += len(batch)
                    batch.clear()
                    print(f"  {n:,} rows", end="\r")
            if batch:
                copy.write("".join(batch))
                n += len(batch)
        print(f"  {n:,} rows")

        print("Rebuilding primary key, foreign key and indexes...")
        cur.execute(_ADD_CONSTRAINTS)
        cur.execute("ANALYZE gene_junction_summary")
    conn.commit()
    print(f"Loaded {n:,} rows into gene_junction_summary.")


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
