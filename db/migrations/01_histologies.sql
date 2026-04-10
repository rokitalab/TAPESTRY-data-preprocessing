-- 01_histologies.sql
-- Tables populated by the histologies ETL (pipelines/01_histologies.py).
-- Insert order: cancer → patient → sample

CREATE TABLE IF NOT EXISTS "cancer" (
    "cancer_key"        BIGSERIAL PRIMARY KEY,
    "cancer_group"      TEXT,
    "broad_histology"   TEXT,
    "molecular_subtype" TEXT,
    UNIQUE ("cancer_group", "broad_histology", "molecular_subtype")
);

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
