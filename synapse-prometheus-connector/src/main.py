# coding=utf-8

import json
import os
import signal
import time
import traceback

import requests

import access_token
import config
import metrics
import model
import spark_pools


def write_string_to_path(path, filename, content):
    _path = os.path.join(path, filename)
    os.makedirs(path, exist_ok=True)
    with open(_path, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_spark_application_scrape_configs(application_list, workspace_name, synapse_host, api_version):
    livy_path_template = f'/livyApi/versions/{api_version}' + '/sparkpools/{spark_pool_name}/sessions/{livy_id}/applications/{application_id}'
    metrics_paths = [
        '/metrics/executors/prometheus',
        '/metrics/prometheus',
    ]
    static_configs = []
    for app in application_list:
        livy_path = livy_path_template.format(spark_pool_name=app.spark_pool_name, livy_id=app.livy_id, application_id=app.spark_application_id)
        for metrics_path in metrics_paths:
            static_configs.append(model.PrometheusStaticConfig(
                targets=[ synapse_host ],
                labels={
                    'synapse_api_version': str(api_version),
                    'workspace_name': str(workspace_name),
                    'spark_pool_name': str(app.spark_pool_name),
                    'livy_id': str(app.livy_id),
                    'application_id': str(app.spark_application_id),
                    'name': str(app.name),
                    '__metrics_path__': str(livy_path + metrics_path),
                    '__param_format': 'html',
                    '__scheme__': 'https',
                }
            ))
    return static_configs


def get_spark_applications(synapse_host, synapse_api_version, bearer_token):
    path = '/monitoring/workloadTypes/spark/applications'
    url = f'https://{synapse_host}{path}'
    params = {
        'api-version': synapse_api_version,
        'skip': 0,
        'filter': "(state eq 'submitting') or (state eq 'inprogress')",
    }
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, params=params, headers=headers, timeout=15)
    if response.status_code == 200:
        apps_info = response.json()
        applications = apps_info.get('sparkJobs')
        application_list = []
        if applications:
            for _app in applications:
                app = model.spark_application_from_dict(_app)
                if not app.spark_application_id:
                    continue
                application_list.append(app)
        return application_list
    print(response.json())
    response.raise_for_status()


def token_refresh_by_workspace(workspace_config, workspace_context):
    if not workspace_context or time.time() - workspace_context.get('token_refresh_time', 0) >= workspace_config.token_refresh_interval_sec:
        metrics.token_refresh_count.labels(workspace_name=workspace_config.workspace_name).inc()
        try:
            print('refreshing token...')
            bearer_token = access_token.get_access_token(
                workspace_config.service_principal_name,
                workspace_config.service_principal_password,
                workspace_config.tenant_id,
                workspace_config.resource_uri)
            workspace_context['token_refresh_time'] = int(time.time())
            workspace_context['bearer_token'] = bearer_token
            print('token refreshed.')
            metrics.token_refresh_last_time.labels(workspace_name=workspace_config.workspace_name).set(int(time.time()))
        except:
            metrics.token_refresh_failed_count.labels(workspace_name=workspace_config.workspace_name).inc()
            traceback.print_exc()


def spark_application_discovery_by_workspace(workspace_config, workspace_context):
    if time.time() - workspace_context.get('application_discovery_time', 0) >= workspace_config.spark_application_discovery_interval_sec:
        metrics.application_discovery_count.labels(workspace_name=workspace_config.workspace_name).inc()
        try:
            print('spark application discovery...')
            bearer_token = workspace_context.get('bearer_token')
            if not bearer_token:
                return
            synapse_host = workspace_config.synapse_host()
            synapse_api_version = workspace_config.synapse_api_version
            workspace_name = workspace_config.workspace_name
            with metrics.application_discovery_duration_histogram.labels(workspace_name).time():
                application_list = get_spark_applications(synapse_host, synapse_api_version, bearer_token)
            workspace_scrape_configs = generate_spark_application_scrape_configs(application_list, workspace_name, synapse_host, synapse_api_version)

            if workspace_config.service_discovery_output_folder:
                folder = os.path.join(workspace_config.service_discovery_output_folder, f'workspace/{workspace_name}/')
                write_string_to_path(folder, 'bearer_token', bearer_token)
                write_string_to_path(folder, 'application_discovery.json', model.to_json(workspace_scrape_configs))

            workspace_context['workspace_scrape_configs'] = workspace_scrape_configs
            workspace_context['application_list'] = application_list
            workspace_context['application_discovery_time'] = int(time.time())
            print(f'spark application discovery, found targets: {len(application_list)}.')

            # spark pool metrics
            spark_pool_applications = {}
            for app in application_list:
                spark_pool_applications.setdefault(app.spark_pool_name, 0)
                spark_pool_applications[app.spark_pool_name] += 1
                print(f'{app.spark_pool_name}/sessions/{app.livy_id}/applications/{app.spark_application_id}\tstate:{app.state}')

            for spark_pool_name, application_count in spark_pool_applications.items():
                metrics.application_discovery_target.labels(workspace_name=workspace_name, spark_pool_name=spark_pool_name).set(application_count)

            # spark application metrics
            metrics.application_info._metrics = {}
            metrics.application_submit_time._metrics = {}
            metrics.application_queue_duration._metrics = {}
            metrics.application_running_duration._metrics = {}
            for app in application_list:
                app_base_labels = dict(workspace_name=workspace_name, spark_pool_name=app.spark_pool_name, name=app.name,
                                       application_id=app.spark_application_id, livy_id=app.livy_id)
                metrics.application_info.labels(subscription_id=workspace_config.subscription_id,
                                                resource_group=workspace_config.resource_group,
                                                tenant_id=workspace_config.tenant_id,
                                                **app_base_labels).set(1)
                metrics.application_submit_time.labels(**app_base_labels).set(app.submit_time_seconds)
                metrics.application_queue_duration.labels(**app_base_labels).set(app.queued_duration_seconds)
                metrics.application_running_duration.labels(**app_base_labels).set(app.running_duration_seconds)
        except:
            metrics.application_discovery_failed_count.labels(workspace_name=workspace_config.workspace_name).inc()
            traceback.print_exc()


def spark_pool_metrics_by_workspace(workspace_config, workspace_context):
    if not workspace_config.enable_spark_pools_metadata_metrics:
        return

    if not workspace_context or time.time() - workspace_context.get('spark_pool_metrics_token_refresh_time', 0) >= workspace_config.token_refresh_interval_sec:
        try:
            print('refreshing token for spark pool metrics...')
            bearer_token = access_token.get_access_token(
                workspace_config.service_principal_name,
                workspace_config.service_principal_password,
                workspace_config.tenant_id,
                workspace_config.azure_management_resource_uri)
            workspace_context['spark_pool_metrics_token_refresh_time'] = int(time.time())
            workspace_context['spark_pool_metrics_bearer_token'] = bearer_token
            print('token refreshed for spark pool metrics.')
        except:
            traceback.print_exc()

    bearer_token = workspace_context.get('spark_pool_metrics_bearer_token')
    if bearer_token and time.time() - workspace_context.get('spark_pool_metrics_time', 0) >= 300:
        workspace_context['spark_pool_metrics_time'] = int(time.time())
        try:
            spark_pools_info = spark_pools.get_spark_pools(
                workspace_config.subscription_id,
                workspace_config.resource_group,
                workspace_config.workspace_name,
                bearer_token)
            for sp in spark_pools_info:
                metrics.spark_pool_info.labels(
                    workspace_name=workspace_config.workspace_name,
                    spark_pool_name=sp.name,
                    location=sp.location,
                    spark_version=sp.spark_version,
                    node_count=str(sp.node_count),
                    node_size=str(sp.node_size),
                    provisioning_state=str(sp.provisioning_state),
                    auto_scale_enabled=str(sp.auto_scale_enabled),
                    node_cpu_cores=str(sp.node_cpu_cores),
                    node_memory_size=str(sp.node_memory_size),
                ).set(1)
        except:
            traceback.print_exc()


class GracefulShutdown:
    shutdown = False
    def __init__(self):
            signal.signal(signal.SIGINT, self.set_shutdown)
            signal.signal(signal.SIGTERM, self.set_shutdown)

    def set_shutdown(self, signum, frame):
            self.shutdown = True


def main():
    graceful_shutdown = GracefulShutdown()

    cfg = config.read_config(filename='config/config.yaml')
    print('started, config loaded.')

    workspace_contexts = {}
    global_context = {}

    while not graceful_shutdown.shutdown:
        for workspace_config in cfg.workspaces:
            workspace_context = workspace_contexts.setdefault(workspace_config.workspace_name, {})
            try:
                token_refresh_by_workspace(workspace_config, workspace_context)
                spark_application_discovery_by_workspace(workspace_config, workspace_context)
                spark_pool_metrics_by_workspace(workspace_config, workspace_context)
            except:
                traceback.print_exc()
        time.sleep(1)


if __name__ == "__main__":
    main()
