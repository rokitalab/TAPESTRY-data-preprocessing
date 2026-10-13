# TAPESTRY data-preprocessing
Repository for pre-processing of PBTA molecular & clinical data for TAPESTRY ingestion.

## Documentation

Table documentation:

| Doc | Tables | Migration | Pipeline |
|---|---|---|---|
| [Histology tables](doc/histology-tables.md) | `patient`, `sample` | `01_histologies.sql` | `pipelines/01_histologies.py` |
| [TEJ tables](doc/tej-tables.md) | `tej`, `tej_domain`, `sample_tej`, `tej_recurrence` | `02_tej.sql` | `pipelines/02_tej.py` |
| [TEJ CPM tables](doc/tej-cpm-tables.md) | `tej_cpm` | `03_tej_cpm.sql` | `pipelines/03_tej_cpm.py` |
| [Summary views](doc/summaries.md) | `tej_gene_summary`, `tej_histology_summary` | `04_summaries.sql` | `pipelines/refresh_views.py` |
| [Gene junction summary](doc/gene-junction-summary.md) | `plot_group`, `gene_junction_summary` | `05_gene_junction_summary.sql` | `pipelines/05_gene_junction_summary.py` |

See also [release notes](doc/release-notes.md) and [migrations](db/migrations/README.md).

## Running with Docker

### Usage

Clone the repository:

```bash
git clone git@github.com:rokitalab/TAPESTRY-data-preprocessing.git
cd TAPESTRY-data-preprocessing
```

Download data files to `data/` (required for pipeline execution):
```bash
bash download_data.sh
```

### Run with local PostgreSQL

Starts a local PostgreSQL instance, applies migrations, loads the histologies and TEJ pipelines, and prints a status summary:

```bash
docker compose up pipeline
```

No `.env` file is needed for Docker Compose — the defaults match the Compose postgres service. 

To stop and remove containers and volumes:

```bash
docker compose down -v
``` 
