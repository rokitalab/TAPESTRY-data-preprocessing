# db/migrations

SQL migrations applied sequentially by the seed runner (`db/seed.py`).

Naming convention: 2-digit prefix, ordered:

| File | Description |
|------|-------------|
| `01_histologies.sql` | Creates `patient` and `sample` tables with indexes |
| `02_tej.sql` | Creates `tej`, `tej_domain`, `sample_tej`, and `tej_recurrence` tables with indexes |
| `03_tej_cpm.sql` | Creates `tej_cpm` table (junction × sample CPM values) with indexes |
| `04_summaries.sql` | Creates `tej_gene_summary` and `tej_histology_summary` materialized views with indexes |

Each file should be idempotent where possible (`CREATE TABLE IF NOT EXISTS`, etc.).
