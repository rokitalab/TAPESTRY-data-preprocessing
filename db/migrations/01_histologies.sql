-- 01_histologies.sql
-- Tables populated by the histologies ETL (pipelines/01_histologies.py).
-- Insert order: patient → sample

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
    "biospecimen_id"    TEXT PRIMARY KEY,
    "patient_id"        TEXT REFERENCES "patient"("patient_id") ON DELETE CASCADE,
    "sample_id"		TEXT,
    "cancer_group"      TEXT,
    "molecular_subtype" TEXT,
    "match_id"          TEXT,
    "resection"         TEXT,
    "primary_site"      TEXT,
    "cns_region"        TEXT,
    "plot_group"        TEXT,
    "cohort"            TEXT,
    "sub_cohort"        TEXT,
    "rna_library"       TEXT,
    "composition"            TEXT,
    "tumor_descriptor"       TEXT,
    "is_independent_primary" BOOLEAN
);

CREATE INDEX IF NOT EXISTS sample_patient_id_idx ON sample (patient_id);
CREATE INDEX IF NOT EXISTS sample_cohort_idx ON sample (cohort);
CREATE INDEX IF NOT EXISTS sample_cancer_group_idx ON sample (cancer_group);
CREATE INDEX IF NOT EXISTS sample_rna_library_idx ON sample (rna_library);
