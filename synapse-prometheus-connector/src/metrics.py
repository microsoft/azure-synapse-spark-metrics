# coding=utf-8

# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from prometheus_client import Counter, Gauge, Histogram, Summary, Info
from prometheus_client import start_http_server


application_base_labelnames = ('workspace_name', 'spark_pool_name', 'name', 'application_id', 'livy_id')
application_extra_labelnames = ('tenant_id', 'subscription_id', 'resource_group')


# metrics by workspace, application
application_info = Gauge(
    'synapse_connector_application_info',
    'synapse_connector_application_info',
    labelnames=application_base_labelnames + application_extra_labelnames)

application_submit_time = Gauge(
    'synapse_connector_application_submit_time',
    'synapse_connector_application_submit_time',
    labelnames=application_base_labelnames)

application_queue_duration = Gauge(
    'synapse_connector_application_queue_duration',
    'synapse_connector_application_queue_duration',
    labelnames=application_base_labelnames)

application_running_duration = Gauge(
    'synapse_connector_application_running_duration',
    'synapse_connector_application_running_duration',
    labelnames=application_base_labelnames)

# metrics workspace_name
token_refresh_last_time = Gauge(
    'synapse_connector_token_refresh_last_time',
    'synapse_connector_token_refresh_last_time',
    labelnames=('workspace_name',))

token_refresh_count = Gauge(
    'synapse_connector_token_refresh_count',
    'synapse_connector_token_refresh_count',
    labelnames=('workspace_name',))

token_refresh_failed_count = Gauge(
    'synapse_connector_token_refresh_failed_count',
    'synapse_connector_token_refresh_failed_count',
    labelnames=('workspace_name',))

application_discovery_target = Gauge(
    'synapse_connector_application_discovery_target',
    'synapse_connector_application_discovery_target',
    labelnames=('workspace_name', 'spark_pool_name'))

application_discovery_count = Gauge(
    'synapse_connector_application_discovery_count',
    'synapse_connector_application_discovery_count',
    labelnames=('workspace_name',))

application_discovery_failed_count = Gauge(
    'synapse_connector_application_discovery_failed_count',
    'synapse_connector_application_discovery_failed_count',
    labelnames=('workspace_name',))

application_discovery_duration_histogram = Histogram(
    'synapse_connector_application_discovery_duration',
    'synapse_connector_application_discovery_duration',
    labelnames=('workspace_name',),
    buckets=(.1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, float('INF')))


# metrics spark pools
spark_pool_base_labelnames = ('workspace_name', 'spark_pool_name')
spark_pool_info_labelnames = ('location', 'spark_version', 'node_count', 'node_size', 'provisioning_state', 'auto_scale_enabled', 'node_cpu_cores', 'node_memory_size')
spark_pool_info = Gauge(
    'synapse_connector_spark_pool_info',
    'synapse_connector_spark_pool_info',
    labelnames=spark_pool_base_labelnames + spark_pool_info_labelnames)


start_http_server(8000)