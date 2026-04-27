# TAPESTRY data-preprocessing
Repository for pre-processing of PBTA molecular & clinical data for TAPESTRY ingestion.

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

Starts a local PostgreSQL instance, applies migrations, loads the histologies pipeline, and prints a status summary:

```bash
docker compose up pipeline
```

No `.env` file is needed for Docker Compose — the defaults match the Compose postgres service. 

To stop and remove containers and volumes:

```bash
docker compose down -v
``` 
