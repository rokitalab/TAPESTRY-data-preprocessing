# Histology Tables

One row per biospecimen. Covers both tumor samples (from `cohort-histologies.tsv`) and control samples (from `control-cohort-histologies.tsv`).

## DDL (from `db/migrations/01_histologies.sql`)

```sql
CREATE TABLE IF NOT EXISTS "sample" (
    "biospecimen_id"   TEXT PRIMARY KEY,
    "patient_id"       TEXT REFERENCES "patient"("patient_id") ON DELETE CASCADE,
    "cancer_key"       BIGINT REFERENCES "cancer"("cancer_key"),
    "match_id"         TEXT,
    "resection"        TEXT,
    "primary_site"     TEXT,
    "cns_region"       TEXT,
    "plot_group"       TEXT,
    "cohort"           TEXT,
    "sub_cohort"       TEXT,
    "rna_library"      TEXT,
    "composition"      TEXT,
    "tumor_descriptor" TEXT
);
```

## Columns

| Column | Type | Tumor source | Control source | Notes |
|---|---|---|---|---|
| `biospecimen_id` | TEXT PK | `Kids_First_Biospecimen_ID` | `sample_id` | |
| `patient_id` | TEXT FK | `Kids_First_Participant_ID` | `Kids_First_Participant_ID` from secondary file | Nullable — NULL for controls with no participant record |
| `cancer_key` | BIGINT FK | derived from `cancer` table | — | Always NULL for controls |
| `match_id` | TEXT | `match_id` | — | |
| `resection` | TEXT | `extent_of_tumor_resection` | — | |
| `primary_site` | TEXT | `primary_site` | `primary_site` from secondary file | |
| `cns_region` | TEXT | `CNS_region` | — | |
| `plot_group` | TEXT | `plot_group` | `subgroup` | |
| `cohort` | TEXT | `cohort` | `cohort` | |
| `sub_cohort` | TEXT | `sub_cohort` | `subgroup` | |
| `rna_library` | TEXT | `RNA_library` | `RNA_library` | `stranded` normalized to `total RNA stranded` |
| `composition` | TEXT | `composition` | `composition` from secondary file | |
| `tumor_descriptor` | TEXT | `tumor_descriptor` | — | |

`"NA"` strings and blanks are coerced to `NULL` by the ETL.

## Relationships

```
patient    (patient_id)  ←── sample.patient_id   (nullable)
cancer     (cancer_key)  ←── sample.cancer_key   (nullable)
```

## Control sample sources

Control samples in `control-cohort-histologies.tsv` carry minimal metadata (`sample_id`, `cohort`, `subgroup`, `RNA_library`). Patient and site information is enriched from secondary files:

| Secondary file | Cohort | Lookup key |
|---|---|---|
| `data/histologies.tsv` | GTEx | `Kids_First_Biospecimen_ID` |
| `data/evodevo-histologies.tsv` | Evo-devo | `Kids_First_Biospecimen_ID` |
| `data/ped-normal-brain-histologies.tsv` | Ped Normal Brain | `Kids_First_Biospecimen_ID` or `sample_id` |
| `data/GSE73721-normal-histologies.tsv` | Pediatric brain cell type | no participant ID — `patient_id = NULL` |

## ETL

Populated by `pipelines/01_histologies.py`. Insert order: `cancer → patient → sample`.

All input file paths are hardcoded in the pipeline. Tumor and control rows are loaded in a single transaction.

**Local:**
```bash
python -m pipelines.01_histologies
```

**Docker** (migrates, loads, and status checks in one step):
```bash
docker compose up pipeline
```
