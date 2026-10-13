# Gene Junction Summary Tables

Genome-wide splice-junction expression summarized per gene, junction and plot group. Unlike `tej_cpm`, this covers every junction that falls in an annotated gene, not just the curated TEJ set. It also stores per-group summary statistics rather than per-sample rows.

Built from the raw STAR merged splice-junction file (`SJ.merged.tsv.gz`, v3 release; see `doc/release-notes.md`).

## DDL (from `db/migrations/05_gene_junction_summary.sql`)

```sql
CREATE TABLE IF NOT EXISTS "plot_group" (
    "id"    SMALLSERIAL PRIMARY KEY,
    "name"  TEXT NOT NULL UNIQUE
);

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
```

The primary key, foreign key and indexes are not in the migration. `pipelines/05_gene_junction_summary.py` rebuilds them after each bulk load:

```sql
ALTER TABLE gene_junction_summary ADD CONSTRAINT gene_junction_summary_pkey
    PRIMARY KEY (gene_symbol, chr, intron_start, intron_end, plot_group_id);
ALTER TABLE gene_junction_summary ADD CONSTRAINT gene_junction_summary_plot_group_id_fkey
    FOREIGN KEY (plot_group_id) REFERENCES plot_group (id);
CREATE INDEX gene_junction_summary_gene_symbol_idx ON gene_junction_summary (gene_symbol);
CREATE INDEX gene_junction_summary_plot_group_id_idx ON gene_junction_summary (plot_group_id);
```

## plot_group columns

Lookup table for plot group names (75 in v3). It is kept separate so that the name isn't repeated on every summary row and in the primary key index.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLSERIAL PK | |
| `name` | TEXT UNIQUE | Group label; see [Group assignment](#group-assignment) |

## gene_junction_summary columns

One row per `(gene_symbol, chr, intron_start, intron_end, plot_group_id)`. v3: 64,855,676 rows across 49,328 genes.

| Column | Type | Notes |
|---|---|---|
| `gene_symbol` | TEXT | GENCODE v39 `gene_name`. A junction is attributed to every gene overlapping either intron end on the same strand |
| `chr` | TEXT | |
| `intron_start` | INTEGER | STAR intron start |
| `intron_end` | INTEGER | STAR intron end |
| `strand` | TEXT | STAR strand call (`1` → `+`, `2` → `-`); NULL when STAR left it undefined |
| `annotated` | BOOLEAN | STAR `annotated` flag |
| `plot_group_id` | SMALLINT FK | References `plot_group.id` |
| `num_samples_detected` | INTEGER | Samples in the group with at least one read at this junction |
| `median_cpm` | REAL | Median CPM over **all** samples in the group, with samples that have no reads counted as 0 |
| `mean_cpm` | REAL | Mean CPM over all samples in the group (same zero-padding). Useful where `median_cpm` is 0 because fewer than half the group has the junction |
| `total_reads` | INTEGER | Sum of unique reads across the group |

CPM = `unique_reads / library_size × 1e6`. Library size is the per-sample total of unique reads across every junction row in `SJ.merged.tsv.gz`.

## Group assignment

Samples are read from `data/cohort-histologies.tsv` and `data/control-cohort-histologies.tsv`, not from the `sample` table. Samples are dropped if they have no plot group or if `is_independent_primary` is explicitly false. Group labels follow the frontend's `collapseControlGroup()` in `PlotArea.jsx`:

- **Evo-devo** timepoint groups collapse to `Forebrain (Prenatal)`, `Forebrain (Postnatal)`, `Hindbrain (Prenatal)` and `Hindbrain (Postnatal)`. Evo-devo samples also keep their raw per-timepoint group as a second membership.
- **GTEx** `Brain - X` groups collapse to `X`. Basal ganglia regions collapse to `Basal Ganglia`.
- **Control groups** are suffixed with their cohort's facet label so that collapsed names don't collide across cohorts. For example, `Cerebellum (GTEx <40)` and `Cerebellum (Pediatric Brain)`. Facet labels: `GTEx <40`, `Evo-devo`, `Pediatric Brain`, `Cell of Origin`. The raw Evo-devo timepoint memberships are not suffixed.

A sample can therefore count toward more than one group.

## Relationships

```
plot_group (id) ←── gene_junction_summary.plot_group_id
```

`gene_symbol` is not a foreign key; it isn't limited to the genes in `tej`.

## ETL

Three steps. The first two are long passes over a 23 GB file and need no database connection. Their outputs are published in the v3 release, so normally only step 3 needs to run.

| Step | Script | Input | Output |
|---|---|---|---|
| 1 | `pipelines/sj_library_size.py` (~35–40 min) | `data/v3/SJ.merged.tsv.gz` | `data/v3/library_sizes.tsv` |
| 2 | `pipelines/gene_junction_summary_compute.py` (~45–90 min) | `SJ.merged.tsv.gz`, `library_sizes.tsv`, `data/gencode.v39.primary_assembly.annotation.gtf.gz`, histologies files | `data/v3/gene_junction_summary.tsv` |
| 3 | `pipelines/05_gene_junction_summary.py` | `data/v3/gene_junction_summary.tsv.gz` | `plot_group`, `gene_junction_summary` |

`SJ.merged.tsv.gz` is not in the release's `md5sum.txt`, so `download_data.sh` does not fetch it. It is only needed to recompute steps 1–2. In that case, download it by hand into `data/v3/`:

```bash
curl -k https://s3.amazonaws.com/bti-openaccess-us-east-1-prd-rokita-lab/tapestry/v3/SJ.merged.tsv.gz -o data/v3/SJ.merged.tsv.gz
```

Step 3 is a full reload in one transaction. It resolves plot group names to IDs (adding new `plot_group` rows as needed), truncates the table and drops its constraints and indexes. It then loads the rows with `COPY` and rebuilds the constraints and indexes. If the load fails, the table rolls back to its previous contents. The table is locked against reads while the load runs.

```bash
python -m pipelines.sj_library_size                 # optional: recompute library sizes
python -m pipelines.gene_junction_summary_compute   # optional: recompute summary
python -m pipelines.05_gene_junction_summary        # load
```

`pipelines/cleanup_antisense_gene_junctions.py` is a one-off cleanup for rows loaded before step 2 started checking strand. It deletes junctions that had been attributed to antisense genes. Run it as a dry run first, then add `--execute`. A fresh load from the current pipeline doesn't need it.
