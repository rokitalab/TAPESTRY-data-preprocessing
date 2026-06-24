#!/usr/bin/env python3
"""
cleanup_antisense_gene_junctions.py

One-off cleanup for gene_junction_summary rows written before
gene_junction_summary_compute.py started checking a junction's STAR strand
call against its gene's annotated strand (see that module's _genes_at).
Those rows attributed a junction to every gene whose interval merely
overlapped it, including antisense genes on the opposite strand -- this
deletes exactly the rows where that happened.

Reuses gene_junction_summary_compute.py's own GTF parsing
(_load_gene_intervals) as the source of truth for each gene's strand, so the
notion of "mismatched" here matches the fixed pipeline's logic exactly.
(gene_symbol, chr) pairs that resolve to more than one strand in the GTF
(a handful of reused symbols) are skipped rather than guessed at. Rows with
a NULL strand (STAR left the junction's strand undefined) are left alone --
there's no strand call to contradict the gene's strand.

Defaults to a dry run that only reports the row count; pass --execute to
actually delete them.

Run:
  python -m pipelines.cleanup_antisense_gene_junctions            # dry run
  python -m pipelines.cleanup_antisense_gene_junctions --execute  # deletes
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from db.connection import get_connection
from pipelines.gene_junction_summary_compute import _load_gene_intervals


def _gene_strand_lookup() -> list[tuple[str, str, str]]:
    """(gene_symbol, chr, strand) for every (gene_symbol, chr) pair that
    resolves to a single strand in the GTF."""
    index = _load_gene_intervals()
    strands: dict[tuple[str, str], set[str]] = defaultdict(set)
    for chrom, (_, ivs, _) in index.items():
        for _, _, name, strand in ivs:
            strands[(name, chrom)].add(strand)

    lookup: list[tuple[str, str, str]] = []
    skipped = 0
    for (name, chrom), s in strands.items():
        if len(s) == 1:
            lookup.append((name, chrom, next(iter(s))))
        else:
            skipped += 1
    if skipped:
        print(f"  Skipping {skipped:,} (gene_symbol, chr) pairs with ambiguous strand in the GTF.")
    return lookup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually delete the rows. Without this flag, only reports the count that would be deleted.",
    )
    args = parser.parse_args()

    print("Loading gene strand lookup from GTF...")
    lookup = _gene_strand_lookup()
    print(f"  {len(lookup):,} unambiguous (gene_symbol, chr) -> strand pairs.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TEMP TABLE gene_strand_lookup (
                    gene_symbol TEXT,
                    chr         TEXT,
                    strand      TEXT,
                    PRIMARY KEY (gene_symbol, chr)
                ) ON COMMIT DROP
                """
            )
            cur.executemany(
                "INSERT INTO gene_strand_lookup (gene_symbol, chr, strand) VALUES (%s, %s, %s)",
                lookup,
            )

            cur.execute(
                """
                SELECT COUNT(*)
                FROM gene_junction_summary g
                JOIN gene_strand_lookup s
                  ON g.gene_symbol = s.gene_symbol AND g.chr = s.chr
                WHERE g.strand IS NOT NULL AND g.strand <> s.strand
                """
            )
            n = cur.fetchone()[0]
            print(f"{n:,} gene_junction_summary rows have a strand that contradicts their gene's annotated strand.")

            if args.execute:
                cur.execute(
                    """
                    DELETE FROM gene_junction_summary g
                    USING gene_strand_lookup s
                    WHERE g.gene_symbol = s.gene_symbol
                      AND g.chr = s.chr
                      AND g.strand IS NOT NULL
                      AND g.strand <> s.strand
                    """
                )
                conn.commit()
                print(f"Deleted {n:,} rows.")
            else:
                conn.rollback()
                print("Dry run -- no rows deleted. Re-run with --execute to delete them.")


if __name__ == "__main__":
    main()
