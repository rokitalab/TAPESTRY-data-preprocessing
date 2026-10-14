# db/migrations

SQL migrations applied sequentially by the migration runner (`python -m db.migrate`).

Naming convention: 2-digit prefix, ordered:

| File | Description |
|------|-------------|
| `01_histologies.sql` | Creates `patient` and `sample` tables with indexes |
| `02_tej.sql` | Creates `tej`, `tej_domain`, `sample_tej`, and `tej_recurrence` tables with indexes |
| `03_tej_cpm.sql` | Creates `tej_cpm` table (junction × sample CPM values); PK, FKs and index are added by `pipelines/03_tej_cpm.py` after load |
| `04_summaries.sql` | Creates `tej_gene_summary` and `tej_histology_summary` materialized views with indexes |
| `05_gene_junction_summary.sql` | Creates `plot_group` lookup and `gene_junction_summary` tables; PK, FK and indexes are added by `pipelines/05_gene_junction_summary.py` after load |

Each file should be idempotent where possible (`CREATE TABLE IF NOT EXISTS`, etc.).
