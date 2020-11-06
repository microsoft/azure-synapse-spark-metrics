# coding=utf-8

from typing import Any, List, Optional

import requests
from attr import attrs

_node_size_mapping = {
    'Small': (4, 32),
    'Medium': (8, 64),
    'Large': (16, 128),
    'XLarge': (32, 256),
    'XXLarge': (64, 432),
}

@attrs(auto_attribs=True)
class SparkPool(object):
    name: str
    location: Optional[str]
    spark_version: Optional[str]
    node_count: Optional[int]
    node_size: Optional[str]
    provisioning_state: Optional[str]
    auto_scale_enabled: bool

    @property
    def node_cpu_cores(self):
        if self.node_size and self.node_size in _node_size_mapping:
            return _node_size_mapping[self.node_size][0]
        return 0

    @property
    def node_memory_size(self):
        if self.node_size and self.node_size in _node_size_mapping:
            return _node_size_mapping[self.node_size][1]
        return 0


def get_spark_pools(subscription_id, resource_group, workspace_name, bearer_token):
    assert subscription_id
    assert resource_group
    assert workspace_name
    api_version = '2019-06-01-preview'
    url = f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Synapse/workspaces/{workspace_name}/bigDataPools'
    params = {
        'api-version': api_version
    }
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, params=params, headers=headers, timeout=15)
    response.raise_for_status()
    spark_pools_obj = response.json()
    value = spark_pools_obj.get('value')
    result = []
    if value:
        for item in value:
            result.append(_convert_spark_pool_result(item))
    return result


def _convert_spark_pool_result(spark_pool_obj):
    properties = spark_pool_obj.get('properties', {})
    auto_scale = properties.get('autoScale')
    return SparkPool(
        name=spark_pool_obj.get('name'),
        location=spark_pool_obj.get('location'),
        spark_version=properties.get('sparkVersion'),
        node_count=properties.get('nodeCount'),
        node_size=properties.get('nodeSize'),
        provisioning_state=properties.get('provisioningState'),
        auto_scale_enabled=bool(auto_scale.get('enabled')) if auto_scale else False
    )
