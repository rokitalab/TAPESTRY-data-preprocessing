# TESJ CPM Tables

Per-sample CPM values for tumor-enriched and oncofetal splice junctions. Built from two RDS matrices — one for tumor samples, one for controls.

## DDL (from `db/migrations/03_tesj_cpm.sql`)

```sql
CREATE TABLE IF NOT EXISTS "tesj_cpm" (
    "junction"       TEXT NOT NULL REFERENCES "tesj"("junction") ON DELETE CASCADE,
    "biospecimen_id" TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "cpm"            REAL,
    PRIMARY KEY ("junction", "biospecimen_id")
);

CREATE INDEX ON tesj_cpm (biospecimen_id);
```

## tesj_cpm columns

One row per `(junction, biospecimen_id)` pair.

| Column | Type | Source | Notes |
|---|---|---|---|
| `junction` | TEXT FK | column header / row key | References `tesj.junction` |
| `biospecimen_id` | TEXT FK | column header | References `sample.biospecimen_id` |
| `cpm` | REAL | matrix cell value | NULL where source value is R `NA`; `0.0` is a valid measurement |

## Relationships

```
tesj   (junction)       ←── tesj_cpm.junction
sample (biospecimen_id) ←── tesj_cpm.biospecimen_id
```

## ETL

Populated by `pipelines/03_tesj_cpm.py` from two source files:

| File | Samples | Notes |
|---|---|---|
| `data/v2/tumor-enriched-oncofetal-splice-junction-cpm.rds` | 1,976 (`BS_*` Kids First IDs) | Tumor cohort |
| `data/v2/tumor-enriched-oncofetal-splice-junction-cpm-ctrls.rds` | 241 (GTEx IDs) | Controls; all IDs present in `sample` table |

Both files are `data.table` / `data.frame` objects with junctions as rows and `biospecimen_id` as columns. The pipeline reads each via `Rscript --vanilla`, unpivots from wide to long with pandas `melt`, and inserts in batches of 50,000 rows.

R `NA` values are coerced to `NULL`; they are not stored as IEEE NaN. A `cpm` of `0.0` means the junction was detected with zero counts — it is distinct from `NULL`.

Scale: ~10,676 junctions × 2,217 samples ≈ 23.7M rows total.

```bash
python -m pipelines.03_tesj_cpm
```
