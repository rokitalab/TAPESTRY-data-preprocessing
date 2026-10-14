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
    "sample_id"              TEXT,
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

CREATE INDEX IF NOT EXISTS sample_patient_id_idx ON sample (patient_id);
CREATE INDEX IF NOT EXISTS sample_cohort_idx ON sample (cohort);
CREATE INDEX IF NOT EXISTS sample_cancer_group_idx ON sample (cancer_group);
CREATE INDEX IF NOT EXISTS sample_rna_library_idx ON sample (rna_library);
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

v3 load: 2,203 samples (1,962 tumor, 241 control) from 1,744 patients.

| Cohort | Samples |
|---|---|
| PBTA | 1,962 |
| GTEx | 113 |
| Evo-devo | 106 |
| Pediatric brain cell type | 15 |
| Pediatric brain | 7 |

| Column | Type | Tumor source | Control source | Notes |
|---|---|---|---|---|
| `biospecimen_id` | TEXT PK | `Kids_First_Biospecimen_ID` | `sample_id` | |
| `patient_id` | TEXT FK | `Kids_First_Participant_ID` | `Kids_First_Participant_ID` from secondary file | Nullable — NULL for controls with no participant record (the 15 Pediatric brain cell type samples) |
| `sample_id` | TEXT | `sample_id` | — | Always NULL for controls |
| `cancer_group` | TEXT | `cancer_group` | — | Always NULL for controls; also NULL for some tumors (301 NULL in v3: 241 controls + 60 tumors) |
| `molecular_subtype` | TEXT | `molecular_subtype` | — | Always NULL for controls |
| `match_id` | TEXT | `match_id` | — | |
| `resection` | TEXT | `extent_of_tumor_resection` | — | |
| `primary_site` | TEXT | `primary_site` | `primary_site` from secondary file | |
| `cns_region` | TEXT | `CNS_region` | — | |
| `plot_group` | TEXT | `plot_group` | `subgroup` | |
| `cohort` | TEXT | `cohort` | `cohort` | |
| `sub_cohort` | TEXT | `sub_cohort` | `subgroup` | |
| `rna_library` | TEXT | `RNA_library` | `RNA_library` | `stranded` normalized to `total RNA stranded`. v3 values: `total RNA stranded` (1,040), `poly-A stranded` (905), `poly-A` (258) |
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
| `data/ped-normal-brain-histologies.tsv` | Pediatric brain | `Kids_First_Biospecimen_ID` or `sample_id` |

Pediatric brain cell type controls have no secondary file and no participant ID, so they are loaded with `patient_id = NULL` and no `primary_site` or `composition`.

## ETL

Populated by `pipelines/01_histologies.py`. Insert order: `patient → sample`.

All input file paths are hardcoded in the pipeline. Tumor and control rows are loaded in a single transaction.

```bash
python -m pipelines.01_histologies
```
