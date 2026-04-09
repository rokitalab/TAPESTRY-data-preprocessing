FROM rocker/tidyverse:4.4.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN Rscript -e "install.packages('qs2', repos='https://cran.r-project.org')"

WORKDIR /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


CMD ["bash", "-c", "pip list && echo '---' && Rscript -e 'installed.packages()[,1]'"]
