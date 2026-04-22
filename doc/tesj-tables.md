# TESJ Tables

Tumor-enriched and oncofetal splice junction data. Built from the recurrent primary-tumor file (`recurrent-primary-tumor-enriched-oncofetal-splice-junctions-annotated.tsv.gz`).

## DDL (from `db/migrations/02_tesj.sql`)

```sql
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
    "id"                SERIAL PRIMARY KEY,
    "junction"          TEXT NOT NULL REFERENCES "tesj"("junction") ON DELETE CASCADE,
    "domain_source"     TEXT NOT NULL,
    "domain_type"       TEXT,
    "domain_name"       TEXT,
    "domain_description" TEXT,
    "domain_start"      INTEGER,
    "domain_end"        INTEGER,
    "overlap_type"      TEXT,
    "overlaps_domain"   BOOLEAN
);

CREATE TABLE IF NOT EXISTS "sample_tesj" (
    "biospecimen_id"    TEXT NOT NULL REFERENCES "sample"("biospecimen_id") ON DELETE CASCADE,
    "junction"          TEXT NOT NULL REFERENCES "tesj"("junction") ON DELETE CASCADE,
    "junction_cpm"      REAL,
    "gene_tpm"          REAL,
    "junction_count"    INTEGER,
    "event_type_sample" TEXT,
    PRIMARY KEY ("biospecimen_id", "junction")
);
```

## tesj columns

| Column | Type | Source | Notes |
|---|---|---|---|
| `junction` | TEXT PK | `junction` | e.g. `chr10:116862799-116862852_116868650-116868706` |
| `chr` | TEXT | `chr` | |
| `strand` | TEXT | `strand` | Constrained to `+` or `-` |
| `gene_symbol` | TEXT | `gene_symbol` | |
| `boundary` | TEXT | `boundary` | Exon boundary coordinates |
| `up_jc_start` | INTEGER | `up_jc_start` | |
| `up_jc_end` | INTEGER | `up_jc_end` | |
| `down_jc_start` | INTEGER | `down_jc_start` | |
| `down_jc_end` | INTEGER | `down_jc_end` | |
| `in_cds` | BOOLEAN | `in_cds` | `Yes` → `TRUE` |
| `consequence` | TEXT | `consequence` | |
| `consensus_jc_event_type` | TEXT | `consensus_jc_event_type` | |
| `junction_preference` | TEXT | `junction_preference` | `Tumor-enriched` or `Oncofetal` |
| `preference_code` | TEXT | `preference_code` | e.g. `EI`, `ES`, `A3+` |
| `novel_ss` | BOOLEAN | `novel_ss` | `Yes` → `TRUE` |
| `junction_name` | TEXT | `junction_name` | |
| `consensus_specificity` | TEXT | `consensus_specificity` | `Oncofetal` or `Tumor-specific` |
| `status` | TEXT | `status` | `Annotated junction`, `Novel junction`, or `Novel splice site` |
| `min_cpm_fc_all` | REAL | `min_cpm_fc_all` | |
| `min_cpm_fc_postnatal` | REAL | `min_cpm_fc_postnatal` | |
| `min_cpm_snr_all` | REAL | `min_cpm_snr_all` | |
| `min_cpm_snr_postnatal` | REAL | `min_cpm_snr_postnatal` | |
| `max_mean_cpm_all` | REAL | `max_mean_cpm_all` | |
| `max_mean_cpm_postnatal` | REAL | `max_mean_cpm_postnatal` | |

## tesj_domain columns

One row per domain annotation. ~42% of junctions have at least one domain; a junction may have both a pfam and a uniprot entry (two rows).

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL PK | |
| `junction` | TEXT FK | References `tesj.junction` |
| `domain_source` | TEXT | `pfam` or `uniprot` |
| `domain_type` | TEXT | `pfam_id` or `uniprot_domain_type` |
| `domain_name` | TEXT | `pfam_name`; NULL for uniprot rows |
| `domain_description` | TEXT | `pfam_description`; NULL for uniprot rows |
| `domain_start` | INTEGER | `pfam_domain_start` or `uniprot_domain_start` |
| `domain_end` | INTEGER | `pfam_domain_end` or `uniprot_domain_end` |
| `overlap_type` | TEXT | `pfam_domain_overlap_type`; NULL for uniprot rows |
| `overlaps_domain` | BOOLEAN | `junction_overlaps_pfam_domain`; NULL for uniprot rows |

## sample_tesj columns

One row per `(biospecimen_id, junction)` pair.

| Column | Type | Source | Notes |
|---|---|---|---|
| `biospecimen_id` | TEXT FK | `Kids_First_Biospecimen_ID` | References `sample.biospecimen_id` |
| `junction` | TEXT FK | `junction` | References `tesj.junction` |
| `junction_cpm` | REAL | `junction_cpm` | |
| `gene_tpm` | REAL | `gene_tpm` | |
| `junction_count` | INTEGER | `junction_count` | |
| `event_type_sample` | TEXT | `event_type_sample` | |

## Relationships

```
tesj        (junction)       ←── tesj_domain.junction
tesj        (junction)       ←── sample_tesj.junction
sample      (biospecimen_id) ←── sample_tesj.biospecimen_id
```

## ETL

Populated by `pipelines/02_tesj.py`. Insert order: `tesj → tesj_domain → sample_tesj`.

The recurrent file is read in a single pass. Junctions are deduplicated in memory before insertion.

`"NA"` strings and blanks are coerced to `NULL` by the ETL.

```bash
python -m pipelines.02_tesj
```
