# Histology Tables

One row per biospecimen. Covers both tumor samples (from `cohort-histologies.tsv`) and control samples (from `control-cohort-histologies.tsv`).

## DDL (from `db/migrations/01_histologies.sql`)

```sql
CREATE TABLE IF NOT EXISTS "patient" (
    "patient_id"             TEXT PRIMARY KEY,
    "reported_gender"        TEXT,
    "germline_sex_estimate"  TEXT,
    "age_at_diagnosis_days"  INTEGER,
    "race"                   TEXT,
    "ethnicity"              TEXT,
    "superpopulation"        TEXT,
    "os_status"              TEXT,
    "os_days"                INTEGER,
    "efs_status"             TEXT,
    "efs_days"               INTEGER,
    "cancer_predispositions" TEXT
);

CREATE TABLE IF NOT EXISTS "sample" (
    "biospecimen_id"         TEXT PRIMARY KEY,
    "patient_id"             TEXT REFERENCES "patient"("patient_id") ON DELETE CASCADE,
    "cancer_group"           TEXT,
    "molecular_subtype"      TEXT,
    "match_id"               TEXT,
    "resection"              TEXT,
    "primary_site"           TEXT,
    "cns_region"             TEXT,
    "plot_group"             TEXT,
    "cohort"                 TEXT,
    "sub_cohort"             TEXT,
    "rna_library"            TEXT,
    "composition"            TEXT,
    "tumor_descriptor"       TEXT,
    "is_independent_primary" BOOLEAN
);
```

## Columns

### patient

| Column | Type | Source | Notes |
|---|---|---|---|
| `patient_id` | TEXT PK | `Kids_First_Participant_ID` | |
| `reported_gender` | TEXT | `reported_gender` | |
| `germline_sex_estimate` | TEXT | `germline_sex_estimate` | |
| `age_at_diagnosis_days` | INTEGER | `age_at_diagnosis_days` | |
| `race` | TEXT | `race` | |
| `ethnicity` | TEXT | `ethnicity` | |
| `superpopulation` | TEXT | `predicted_ancestry` | Populated from `somalier-ancestry-prediction-superpopulation.tsv`; NULL for controls |
| `os_status` | TEXT | `OS_status` | NULL for controls |
| `os_days` | INTEGER | `OS_days` | NULL for controls |
| `efs_status` | TEXT | `EFS_status` | NULL for controls |
| `efs_days` | INTEGER | `EFS_days` | NULL for controls |
| `cancer_predispositions` | TEXT | `cancer_predispositions` | NULL for controls |

### sample

| Column | Type | Tumor source | Control source | Notes |
|---|---|---|---|---|
| `biospecimen_id` | TEXT PK | `Kids_First_Biospecimen_ID` | `sample_id` | |
| `patient_id` | TEXT FK | `Kids_First_Participant_ID` | `Kids_First_Participant_ID` from secondary file | Nullable — NULL for controls with no participant record |
| `cancer_group` | TEXT | `cancer_group` | — | Always NULL for controls |
| `molecular_subtype` | TEXT | `molecular_subtype` | — | Always NULL for controls |
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
| `is_independent_primary` | BOOLEAN | `is_independent_primary` | — | `Yes`/`No` mapped to `true`/`false`; always NULL for controls |

`"NA"` strings and blanks are coerced to `NULL` by the ETL.

## Relationships

```
patient (patient_id)  ←── sample.patient_id  (nullable)
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

Populated by `pipelines/01_histologies.py`. Insert order: `patient → sample`.

All input file paths are hardcoded in the pipeline. Tumor and control rows are loaded in a single transaction.

**Local:**
```bash
python -m pipelines.01_histologies
```

**Docker** (migrates, loads, and status checks in one step):
```bash
docker compose up pipeline
```
