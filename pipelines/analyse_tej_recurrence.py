#!/usr/bin/env python3
"""
analyse_tej_recurrence.py

Analyse tej_recurrence percentages.

Run:
  python -m pipelines.analyse_tej_recurrence
"""
from __future__ import annotations

from db.connection import get_connection


def main() -> None:
    print("\n========== TEJ RECURRENCE ANALYSIS ==========\n")
    with get_connection() as conn:
        with conn.cursor() as cur:

            # --- overall pct distribution ---
            cur.execute("""
                SELECT
                    MIN(pct)                     AS min,
                    ROUND(AVG(pct)::numeric, 2)  AS mean,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pct) AS median,
                    MAX(pct)                     AS max,
                    COUNT(*)                     AS total_rows
                FROM tej_recurrence
            """)
            row = cur.fetchone()
            print("Recurrence pct distribution (all plot_groups)")
            print(f"  min:    {row[0]}%")
            print(f"  mean:   {row[1]}%")
            print(f"  median: {row[2]}%")
            print(f"  max:    {row[3]}%")
            print(f"  rows:   {row[4]:,}")

            # --- pct buckets ---
            cur.execute("""
                SELECT
                    CASE
                        WHEN pct >= 50 THEN '>=50%'
                        WHEN pct >= 25 THEN '25-49%'
                        WHEN pct >= 10 THEN '10-24%'
                        WHEN pct >= 5  THEN '5-9%'
                        ELSE '<5%'
                    END AS bucket,
                    COUNT(*) AS n
                FROM tej_recurrence
                GROUP BY 1
                ORDER BY MIN(pct) DESC
            """)
            print("\nRecurrence pct buckets")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]:,}")

            # --- top junctions by max pct across any plot_group ---
            cur.execute("""
                SELECT r.junction, t.gene_symbol, r.plot_group, r.sample_count, r.total_samples, r.pct
                FROM tej_recurrence r
                JOIN tej t USING (junction)
                ORDER BY r.pct DESC
                LIMIT 20
            """)
            print("\nTop 20 junction × plot_group by pct")
            print(f"  {'junction':<55} {'gene':<12} {'plot_group':<30} {'count':>6} {'total':>6} {'pct':>6}")
            for row in cur.fetchall():
                print(f"  {row[0]:<55} {(row[1] or ''):<12} {row[2]:<30} {row[3]:>6} {row[4]:>6} {row[5]:>6}%")

            # --- junctions recurrent in the most plot_groups ---
            cur.execute("""
                SELECT r.junction, t.gene_symbol, COUNT(*) AS n_plot_groups, ROUND(AVG(pct)::numeric, 2) AS avg_pct
                FROM tej_recurrence r
                JOIN tej t USING (junction)
                GROUP BY r.junction, t.gene_symbol
                ORDER BY n_plot_groups DESC, avg_pct DESC
                LIMIT 20
            """)
            print("\nTop 20 junctions by number of plot_groups")
            print(f"  {'junction':<55} {'gene':<12} {'plot_groups':>11} {'avg_pct':>8}")
            for row in cur.fetchall():
                print(f"  {row[0]:<55} {(row[1] or ''):<12} {row[2]:>11} {row[3]:>8}%")

            # --- per plot_group: median pct and junction count ---
            cur.execute("""
                SELECT
                    plot_group,
                    COUNT(*)                                               AS n_junctions,
                    ROUND(AVG(pct)::numeric, 2)                           AS avg_pct,
                    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pct)::numeric, 2) AS median_pct,
                    MAX(pct)                                               AS max_pct
                FROM tej_recurrence
                GROUP BY plot_group
                ORDER BY n_junctions DESC
            """)
            print("\nPer plot_group summary")
            print(f"  {'plot_group':<30} {'junctions':>9} {'avg_pct':>8} {'median_pct':>10} {'max_pct':>8}")
            for row in cur.fetchall():
                print(f"  {row[0]:<30} {row[1]:>9} {row[2]:>8}% {row[3]:>9}% {row[4]:>8}%")


if __name__ == "__main__":
    main()
