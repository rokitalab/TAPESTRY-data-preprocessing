-- 02_tej.sql
-- Tables populated by the TEJ ETL (pipelines/02_tej.py).
-- Insert order: tej → tej_domain → sample_tej → tej_recurrence

CREATE TABLE IF NOT EXISTS "tej" (
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

CREATE TABLE IF NOT EXISTS "tej_domain" (
    "id"              SERIAL PRIMARY KEY,
    "junction"        TEXT NOT NULL REFERENCES "tej"("junction") ON DELETE CASCADE,
    "domain_source"   TEXT NOT NULL,
    "domain_type"     TEXT,
    "domain_name"     TEXT,
    "domain_description" TEXT,
    "domain_start"    INTEGER,
    "domain_end"      INTEGER,
    "overlap_type"    TEXT,
    "overlaps_domain" BOOLEAN
);

CREATE TABLE IF NOT EXISTS "sample_tej" (
    "biospecimen_id"   TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "junction"         TEXT NOT NULL REFERENCES "tej"("junction") ON DELETE CASCADE,
    "junction_cpm"     REAL,
    "gene_tpm"         REAL,
    "junction_count"   INTEGER,
    "event_type_sample" TEXT,
    PRIMARY KEY ("biospecimen_id", "junction")
);

CREATE TABLE IF NOT EXISTS "tej_recurrence" (
    "junction"       TEXT NOT NULL REFERENCES "tej"("junction") ON DELETE CASCADE,
    "plot_group"     TEXT NOT NULL,
    "sample_count"   INTEGER NOT NULL,
    "total_samples"  INTEGER NOT NULL,
    "pct"            REAL NOT NULL,
    PRIMARY KEY ("junction", "plot_group")
);

CREATE INDEX ON tej (gene_symbol);
CREATE INDEX ON tej (junction_preference);
CREATE INDEX ON tej_domain (junction);
CREATE INDEX ON sample_tej (junction);
CREATE INDEX ON tej_recurrence (plot_group);
