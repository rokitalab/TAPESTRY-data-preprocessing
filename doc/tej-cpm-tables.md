# TEJ CPM Tables

Per-sample CPM values for tumor-enriched and oncofetal splice junctions. Built from two CPM matrices (one for tumor samples, one for controls) plus a ComBat batch-corrected matrix for tumors.

## DDL (from `db/migrations/03_tej_cpm.sql`)

```sql
CREATE TABLE IF NOT EXISTS "tej_cpm" (
    "junction"             TEXT NOT NULL,
    "biospecimen_id"       TEXT NOT NULL,
    "cpm"                  REAL,
    "cpm_corrected"        REAL
);
```

The primary key, foreign keys and index are not in the migration. `pipelines/03_tej_cpm.py` adds them after the bulk load, because building them once is much faster than maintaining them across ~97M inserts:

```sql
ALTER TABLE tej_cpm ADD CONSTRAINT tej_cpm_pkey PRIMARY KEY (junction, biospecimen_id);
ALTER TABLE tej_cpm ADD CONSTRAINT tej_cpm_junction_fkey
    FOREIGN KEY (junction) REFERENCES tej (junction) ON DELETE CASCADE;
ALTER TABLE tej_cpm ADD CONSTRAINT tej_cpm_biospecimen_id_fkey
    FOREIGN KEY (biospecimen_id) REFERENCES sample (biospecimen_id) ON DELETE CASCADE;
CREATE INDEX tej_cpm_biospecimen_id_idx ON tej_cpm (biospecimen_id);
```

## tej_cpm columns

One row per `(junction, biospecimen_id)` pair.

| Column | Type | Source | Notes |
|---|---|---|---|
| `junction` | TEXT FK | `junction` column of the matrix | References `tej.junction` |
| `biospecimen_id` | TEXT FK | matrix column header | References `sample.biospecimen_id` |
| `cpm` | REAL | CPM matrix cell value | NULL where source value is R `NA`; `0.0` is a valid measurement |
| `cpm_corrected` | REAL | ComBat-corrected CPM matrix cell value | Batch-corrected, linear scale (not log2); tumor samples only, NULL for all controls |

## Relationships

```
tej    (junction)       ←── tej_cpm.junction
sample (biospecimen_id) ←── tej_cpm.biospecimen_id
```

## ETL

Populated by `pipelines/03_tej_cpm.py` from three source files (v3 release):

| File | Format | Dimensions | Notes |
|---|---|---|---|
| `data/tumor-enriched-oncofetal-splice-junction-cpm.qs2` | qs2 | 45,430 junctions × 1,962 samples | Tumor cohort raw CPM |
| `data/tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds` | RDS | 31,699 junctions × 241 samples | Controls; all IDs present in `sample` table |
| `data/tumor-enriched-oncofetal-splice-junction-cpm-combat-corrected.qs2` | qs2 | 45,430 junctions × 1,962 samples | Tumor cohort CPM, ComBat batch-corrected |

All three files are wide-format `data.frame` objects with a `junction` column and one column per `biospecimen_id`. The pipeline reads each via `Rscript --vanilla` (`readRDS` for RDS, `qs2::qs_read` for qs2), streaming R's output straight into pandas.

The tumor CPM matrix is aligned with the corrected matrix on `(junction, biospecimen_id)`. Each matrix is then unpivoted and bulk-loaded with `COPY`, 1,000 junctions per chunk, so the full long-format table is never held in memory. Controls have `cpm_corrected = NULL`.

The load runs in a single transaction, and `tej_cpm` must be empty before it starts (`TRUNCATE` it to reload). If the load fails, the table is left empty.

R `NA` values are coerced to `NULL`; they are not stored as IEEE NaN. A `cpm` of `0.0` means the junction was detected with zero counts, which is distinct from `NULL`.

Scale (v3):

| | Samples | Rows |
|---|---|---|
| Tumor | 1,962 | 89,133,660 |
| Control | 241 | 7,639,459 |
| **Total** | **2,203** | **96,773,119** |

All 45,430 `tej` junctions and all 2,203 samples are covered. `cpm` distribution: min 0.0, median ≈ 0.037, mean ≈ 0.575, max ≈ 7,720; ~15% of rows are 0.

```bash
python -m pipelines.03_tej_cpm
```
