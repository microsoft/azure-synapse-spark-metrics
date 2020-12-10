# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

FROM python:3.7.9-alpine as base

WORKDIR /app/synapse_connector
ENV AZURE_CONFIG_DIR /app/azurecli

RUN python -m pip install \
    requests \
    python-dateutil \
    attrs \
    cattrs \
    PyYAML \
    prometheus_client \
    timestring

COPY src .

ENTRYPOINT ["python", "main.py"]