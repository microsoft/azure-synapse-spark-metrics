# coding=utf-8

import enum
import typing

import attr
import cattr
import yaml
from attr import attrib, attrs


@attrs(auto_attribs=True)
class SynapseConnectorWorkspaceConfig(object):
    tenant_id: str = attrib()
    service_principal_name: str = attrib()
    service_principal_password: str = attrib()
    workspace_name: str = attrib()
    subscription_id: str = attrib(default='')
    resource_group: str = attrib(default='')
    synapse_host_suffix: str = attrib(default='dev.azuresynapse.net')
    synapse_api_version: str = attrib(default='2019-11-01-preview')
    resource_uri: str = attrib(default='https://dev.azuresynapse.net')
    service_discovery_output_folder: str = attrib(default='output/')
    token_refresh_interval_sec: int = attrib(default=1800)
    spark_application_discovery_interval_sec: int = attrib(default=10)
    azure_management_resource_uri: str = attrib(default='https://management.azure.com')
    enable_spark_pools_metadata_metrics: bool = attrib(default=True)

    def synapse_host(self):
        return '{workspace_name}.{suffix}'.format(workspace_name=self.workspace_name, suffix=self.synapse_host_suffix)


@attrs(auto_attribs=True)
class SynapseConnectorConfig(object):
    workspaces: typing.List[SynapseConnectorWorkspaceConfig] = attrib()
    spark_application_discovery_config_secret_name: str = attrib(default='synapse-application-discovery-config')


def read_config(filename) -> SynapseConnectorConfig:
    with open(filename, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        return cattr.structure(data, SynapseConnectorConfig)
