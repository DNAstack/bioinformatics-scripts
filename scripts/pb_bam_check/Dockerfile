FROM python:3.13-slim

LABEL maintainer="Bioinformatics <bioinformatics@dnastack.com>" \
      version="v0.0.1" \
      description="A Dockerfile for parsing BAM files for methylation and kinetic tags"

ARG IMAGE_TAG
ENV IMAGE_TAG="${IMAGE_TAG}"

RUN apt-get update && apt-get install -y \
  gcc \
  libbz2-dev \
  liblzma-dev \
  libcurl4-openssl-dev \
  zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY hfs_bam_tag_check.py .

RUN chmod 750 hfs_bam_tag_check.py

ENV PATH="/app:${PATH}"

CMD ["/bin/bash"]
