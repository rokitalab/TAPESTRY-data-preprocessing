# TAPESTRY data-preprocessing
Repository for pre-processing of PBTA molecular & clinical data for TAPESTRY ingestion

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

Pull the Docker image:

```bash
docker pull pgc-images.sbgenomics.com/rokita-lab/tapestry:latest
```

Run the container:

```bash
docker run --rm -v .:/app -v ./data:/app/data:ro pgc-images.sbgenomics.com/rokita-lab/tapestry:latest
```

This prints the installed Python and R packages to verify the image and dependencies are installed correctly.

### Run with local PostgreSQL

Pull the image from the registry, starts a local PostgreSQL instance, and runs the pipeline container with the `data/` directory mounted read-only.
```bash
docker compose up
```
