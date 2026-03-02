FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        ninja-build \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    numpy>=1.26 \
    scipy>=1.11 \
    stim>=1.15 \
    pymatching>=2.3 \
    scikit-learn>=1.4 \
    pydantic>=2.7

WORKDIR /work
