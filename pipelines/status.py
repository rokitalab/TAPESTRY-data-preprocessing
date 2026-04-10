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
    with get_connection() as conn:
        with conn.cursor() as cur:

            # --- row counts ---
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM cancer)  AS cancer,
                    (SELECT COUNT(*) FROM patient) AS patient,
                    (SELECT COUNT(*) FROM sample)  AS sample
            """)
            counts = cur.fetchone()
            print("Row counts")
            print(f"  cancer:  {counts[0]}")
            print(f"  patient: {counts[1]}")
            print(f"  sample:  {counts[2]}")

            # --- sample: tumor vs control ---
            cur.execute("""
                SELECT
                    CASE WHEN cancer_key IS NOT NULL THEN 'tumor' ELSE 'control' END AS type,
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
                    COUNT(*) FILTER (WHERE patient_id IS NULL) AS no_patient,
                    COUNT(*) FILTER (WHERE cancer_key  IS NULL) AS no_cancer,
                    COUNT(*) FILTER (WHERE rna_library IS NULL) AS no_rna_library
                FROM sample
            """)
            row = cur.fetchone()
            print("\nNulls in sample")
            print(f"  patient_id=NULL:  {row[0]}")
            print(f"  cancer_key=NULL:  {row[1]}")
            print(f"  rna_library=NULL: {row[2]}")


if __name__ == "__main__":
    main()
