-- 05_gene_junction_summary.sql
-- Table populated by the genome-wide junction summary ETL
-- (pipelines/05_gene_junction_summary.py). Unlike tej_cpm, this covers every
-- annotated gene, not just the curated TEJ set, and stores a per-group
-- summary statistic (median CPM) rather than raw per-sample rows.

-- plot_group only has a few dozen distinct values but is part of
-- gene_junction_summary's primary key, so it's normalized into its own
-- lookup table -- storing the ~20-30 char name on every one of the 30M+
-- summary rows (and in the PK index) would roughly double the PK index
-- size for no benefit.
CREATE TABLE IF NOT EXISTS "plot_group" (
    "id"    SMALLSERIAL PRIMARY KEY,
    "name"  TEXT NOT NULL UNIQUE
);

-- The primary key (gene_symbol, chr, intron_start, intron_end, plot_group_id),
-- the foreign key to plot_group, and the gene_symbol / plot_group_id indexes
-- are (re)built by pipelines/05_gene_junction_summary.py after it bulk-loads
-- the table with COPY. Keeping them out of this file also stops repeated
-- `db.migrate` runs from stacking up duplicate unnamed indexes.
CREATE TABLE IF NOT EXISTS "gene_junction_summary" (
    "gene_symbol"          TEXT NOT NULL,
    "chr"                  TEXT NOT NULL,
    "intron_start"         INTEGER NOT NULL,
    "intron_end"           INTEGER NOT NULL,
    "strand"               TEXT CHECK (strand IN ('+', '-') OR strand IS NULL),
    "annotated"            BOOLEAN NOT NULL,
    "plot_group_id"        SMALLINT NOT NULL,
    "num_samples_detected" INTEGER NOT NULL,
    "median_cpm"           REAL NOT NULL,
    "mean_cpm"             REAL NOT NULL,
    "total_reads"          INTEGER NOT NULL
);
