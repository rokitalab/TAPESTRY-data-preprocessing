-- 03_tesj_cpm.sql
-- Tables populated by the TESJ CPM ETL (pipelines/03_tesj_cpm.py).
-- Insert order: tesj_cpm

CREATE TABLE IF NOT EXISTS "tesj_cpm" (
    "junction"       TEXT NOT NULL REFERENCES "tesj"("junction") ON DELETE CASCADE,
    "biospecimen_id" TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "cpm"                  REAL,
    "log2_cpm_corrected"   REAL,
    PRIMARY KEY ("junction", "biospecimen_id")
);

CREATE INDEX ON tesj_cpm (biospecimen_id);
