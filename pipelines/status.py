#!/usr/bin/env python3
"""
status.py

Report row counts and key breakdowns for the histologies tables.

Run:
  python -m pipelines.status
"""
from __future__ import annotations

from db.connection import get_connection


def main() -> None:
    print("\n========== DATABASE STATUS ==========\n")
    with get_connection() as conn:
        with conn.cursor() as cur:

            # --- row counts ---
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM patient) AS patient,
                    (SELECT COUNT(*) FROM sample)  AS sample
            """)
            counts = cur.fetchone()
            print("Row counts")
            print(f"  patient: {counts[0]}")
            print(f"  sample:  {counts[1]}")

            # --- sample: tumor vs control ---
            cur.execute("""
                SELECT
                    CASE WHEN cancer_group IS NOT NULL THEN 'tumor' ELSE 'control' END AS type,
                    COUNT(*) AS n
                FROM sample
                GROUP BY 1
                ORDER BY 1
            """)
            print("\nSample type")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

            # --- sample: by cohort ---
            cur.execute("""
                SELECT cohort, COUNT(*) AS n
                FROM sample
                GROUP BY cohort
                ORDER BY n DESC
            """)
            print("\nSamples by cohort")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

            # --- rna_library breakdown ---
            cur.execute("""
                SELECT rna_library, COUNT(*) AS n
                FROM sample
                GROUP BY rna_library
                ORDER BY n DESC
            """)
            print("\nSamples by rna_library")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

            # --- nulls check ---
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE patient_id   IS NULL) AS no_patient,
                    COUNT(*) FILTER (WHERE cancer_group IS NULL) AS no_cancer_group,
                    COUNT(*) FILTER (WHERE rna_library  IS NULL) AS no_rna_library
                FROM sample
            """)
            row = cur.fetchone()
            print("\nNulls in sample")
            print(f"  patient_id=NULL:    {row[0]}")
            print(f"  cancer_group=NULL:  {row[1]}")
            print(f"  rna_library=NULL:   {row[2]}")

            # --- TEJ row counts ---
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM tej)            AS tej,
                    (SELECT COUNT(*) FROM tej_domain)     AS tej_domain,
                    (SELECT COUNT(*) FROM sample_tej)     AS sample_tej,
                    (SELECT COUNT(*) FROM tej_recurrence) AS tej_recurrence,
                    (SELECT COUNT(*) FROM tej_cpm)        AS tej_cpm
            """)
            counts = cur.fetchone()
            print("\nTEJ row counts")
            print(f"  tej:             {counts[0]}")
            print(f"  tej_domain:      {counts[1]}")
            print(f"  sample_tej:      {counts[2]}")
            print(f"  tej_recurrence:  {counts[3]}")
            print(f"  tej_cpm:         {counts[4]}")

            # --- tej_cpm: coverage ---
            cur.execute("""
                SELECT
                    COUNT(DISTINCT junction)     AS junctions,
                    COUNT(DISTINCT biospecimen_id) AS samples
                FROM tej_cpm
            """)
            row = cur.fetchone()
            print("\ntej_cpm coverage")
            print(f"  unique junctions: {row[0]:,}")
            print(f"  unique samples:   {row[1]:,}")

            # --- tej_cpm: tumor vs control ---
            cur.execute("""
                SELECT
                    CASE WHEN s.cancer_group IS NOT NULL THEN 'tumor' ELSE 'control' END AS type,
                    COUNT(DISTINCT tc.biospecimen_id) AS samples,
                    COUNT(*) AS rows
                FROM tej_cpm tc
                JOIN sample s USING (biospecimen_id)
                GROUP BY 1
                ORDER BY 1
            """)
            print("\ntej_cpm by sample type")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]:,} samples, {row[2]:,} rows")

            # --- tej_cpm: CPM distribution ---
            cur.execute("""
                SELECT
                    MIN(cpm)                                                    AS min,
                    ROUND(AVG(cpm)::numeric, 4)                                AS mean,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cpm)           AS median,
                    MAX(cpm)                                                    AS max,
                    ROUND(100.0 * COUNT(*) FILTER (WHERE cpm = 0) / COUNT(*), 1) AS pct_zero
                FROM tej_cpm
            """)
            row = cur.fetchone()
            print("\ntej_cpm CPM distribution")
            print(f"  min:      {row[0]}")
            print(f"  mean:     {row[1]}")
            print(f"  median:   {row[2]}")
            print(f"  max:      {row[3]}")
            print(f"  zero rows: {row[4]}%")

            # --- tej_cpm: samples present in sample table but absent from tej_cpm ---
            cur.execute("""
                SELECT COUNT(*) FROM sample
                WHERE rna_library IS NOT NULL
                  AND biospecimen_id NOT IN (SELECT DISTINCT biospecimen_id FROM tej_cpm)
            """)
            missing = cur.fetchone()[0]
            print(f"\ntej_cpm missing RNA samples: {missing}")

            # --- TEJ: by junction_preference ---
            cur.execute("""
                SELECT junction_preference, COUNT(*) AS n
                FROM tej
                GROUP BY junction_preference
                ORDER BY n DESC
            """)
            print("\nTEJ by junction_preference")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

            # --- TEJ: by consensus_specificity ---
            cur.execute("""
                SELECT consensus_specificity, COUNT(*) AS n
                FROM tej
                GROUP BY consensus_specificity
                ORDER BY n DESC
            """)
            print("\nTEJ by consensus_specificity")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    main()
