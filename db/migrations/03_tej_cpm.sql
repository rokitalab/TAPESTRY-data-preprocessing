-- 03_tej_cpm.sql
-- Tables populated by the TEJ CPM ETL (pipelines/03_tej_cpm.py).
-- Insert order: tej_cpm

CREATE TABLE IF NOT EXISTS "tej_cpm" (
    "junction"       TEXT NOT NULL REFERENCES "tej"("junction") ON DELETE CASCADE,
    "biospecimen_id" TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "cpm"                  REAL,
    "log2_cpm_corrected"   REAL,
    PRIMARY KEY ("junction", "biospecimen_id")
);

CREATE INDEX ON tej_cpm (biospecimen_id);
