-- 03_tej_cpm.sql
-- Tables populated by the TEJ CPM ETL (pipelines/03_tej_cpm.py).
-- Insert order: tej_cpm
--
-- The primary key (junction, biospecimen_id), the foreign keys to tej and
-- sample, and the biospecimen_id index are added by pipelines/03_tej_cpm.py
-- after it bulk-loads the table with COPY -- building them once after the load
-- is much faster than maintaining them for ~97M individual rows.

CREATE TABLE IF NOT EXISTS "tej_cpm" (
    "junction"             TEXT NOT NULL,
    "biospecimen_id"       TEXT NOT NULL,
    "cpm"                  REAL,
    "cpm_corrected"        REAL
);
