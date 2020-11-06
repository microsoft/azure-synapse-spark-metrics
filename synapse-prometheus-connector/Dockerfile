FROM microsoft/azure-cli:latest as base

WORKDIR /app/synapse_connector
ENV AZURE_CONFIG_DIR /app/azurecli

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl

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