-- 02_tesj.sql
-- Tables populated by the TESJ ETL (pipelines/02_tesj.py).
-- Insert order: tesj → tesj_domain → sample_tesj

CREATE TABLE IF NOT EXISTS "tesj" (
    "junction"               TEXT PRIMARY KEY,
    "chr"                    TEXT,
    "strand"                 TEXT CHECK ("strand" IN ('+', '-')),
    "gene_symbol"            TEXT,
    "boundary"               TEXT,
    "up_jc_start"            INTEGER,
    "up_jc_end"              INTEGER,
    "down_jc_start"          INTEGER,
    "down_jc_end"            INTEGER,
    "in_cds"                 BOOLEAN,
    "consequence"            TEXT,
    "consensus_jc_event_type" TEXT,
    "junction_preference"    TEXT,
    "preference_code"        TEXT,
    "novel_ss"               BOOLEAN,
    "junction_name"          TEXT,
    "consensus_specificity"  TEXT,
    "status"                 TEXT,
    "min_cpm_fc_all"         REAL,
    "min_cpm_fc_postnatal"   REAL,
    "min_cpm_snr_all"        REAL,
    "min_cpm_snr_postnatal"  REAL,
    "max_mean_cpm_all"       REAL,
    "max_mean_cpm_postnatal" REAL
);

CREATE TABLE IF NOT EXISTS "tesj_domain" (
    "id"              SERIAL PRIMARY KEY,
    "junction"        TEXT NOT NULL REFERENCES "tesj"("junction") ON DELETE CASCADE,
    "domain_source"   TEXT NOT NULL,
    "domain_type"     TEXT,
    "domain_name"     TEXT,
    "domain_description" TEXT,
    "domain_start"    INTEGER,
    "domain_end"      INTEGER,
    "overlap_type"    TEXT,
    "overlaps_domain" BOOLEAN
);

CREATE TABLE IF NOT EXISTS "sample_tesj" (
    "biospecimen_id"   TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "junction"         TEXT NOT NULL REFERENCES "tesj"("junction") ON DELETE CASCADE,
    "junction_cpm"     REAL,
    "gene_tpm"         REAL,
    "junction_count"   INTEGER,
    "event_type_sample" TEXT,
    PRIMARY KEY ("biospecimen_id", "junction")
);

CREATE INDEX ON tesj (gene_symbol);
CREATE INDEX ON tesj (junction_preference);
CREATE INDEX ON tesj_domain (junction);
CREATE INDEX ON sample_tesj (junction);
