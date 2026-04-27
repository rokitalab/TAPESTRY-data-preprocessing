# TEJ CPM Tables

Per-sample CPM values for tumor-enriched and oncofetal splice junctions. Built from two RDS matrices — one for tumor samples, one for controls.

## DDL (from `db/migrations/03_tej_cpm.sql`)

```sql
CREATE TABLE IF NOT EXISTS "tej_cpm" (
    "junction"       TEXT NOT NULL REFERENCES "tej"("junction") ON DELETE CASCADE,
    "biospecimen_id" TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "cpm"            REAL,
    PRIMARY KEY ("junction", "biospecimen_id")
);

CREATE INDEX ON tej_cpm (biospecimen_id);
```

## tej_cpm columns

One row per `(junction, biospecimen_id)` pair.

| Column | Type | Source | Notes |
|---|---|---|---|
| `junction` | TEXT FK | column header / row key | References `tej.junction` |
| `biospecimen_id` | TEXT FK | column header | References `sample.biospecimen_id` |
| `cpm` | REAL | CPM matrix cell value | NULL where source value is R `NA`; `0.0` is a valid measurement |
| `log2_cpm_corrected` | REAL | log2 CPM matrix cell value | Batch-corrected; tumor samples only — NULL for all controls |

## Relationships

```
tej   (junction)       ←── tej_cpm.junction
sample (biospecimen_id) ←── tej_cpm.biospecimen_id
```

## ETL

Populated by `pipelines/03_tej_cpm.py` from two source files:

| File | Format | Samples | Notes |
|---|---|---|---|
| `data/v2/tumor-enriched-oncofetal-splice-junction-cpm.rds` | RDS | 1,976 (`BS_*` Kids First IDs) | Tumor cohort raw CPM |
| `data/v2/tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds` | RDS | 241 (GTEx IDs) | Controls; all IDs present in `sample` table |
| `data/v2/tumor-enriched-oncofetal-splice-junction-log2-cpm-combat-corrected.qs2` | qs2 | 1,976 (`BS_*` Kids First IDs) | Tumor cohort log2 CPM, batch-corrected |

All three files are wide-format `data.frame` objects with junctions as rows and `biospecimen_id` as columns. The pipeline reads each via `Rscript --vanilla` (using `readRDS` for RDS files and `qs2::qs_read` for qs2), unpivots from wide to long with pandas `melt`, and inserts in batches of 50,000 rows.

For tumor samples, the raw CPM and log2 corrected CPM files are merged on `(junction, biospecimen_id)` before insertion. Controls have `log2_cpm_corrected = NULL`.

R `NA` values are coerced to `NULL`; they are not stored as IEEE NaN. A `cpm` of `0.0` means the junction was detected with zero counts — it is distinct from `NULL`.

Scale: ~10,676 junctions × 2,217 samples ≈ 23.7M rows total.

```bash
python -m pipelines.03_tej_cpm
```
