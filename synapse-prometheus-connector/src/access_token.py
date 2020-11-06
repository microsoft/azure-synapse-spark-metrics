# coding=utf-8


import io
import json
import shlex
import subprocess

from azure.cli.core import get_default_cli


def az(command):
    stdout = io.StringIO()
    args = shlex.split(command)
    exit_code = get_default_cli().invoke(args, out_file=stdout)
    return exit_code, stdout.getvalue()   


def get_access_token(service_principal_name, service_principal_password, tenant_id, resource_uri):
    exit_code, stdout = az(f'login --service-principal --username "{service_principal_name}" --password "{service_principal_password}" --tenant "{tenant_id}"')
    if exit_code != 0:
        raise Exception('login failed.')

    exit_code, stdout = az(f'account get-access-token --resource {resource_uri}')
    if exit_code != 0:
        raise Exception('get access token failed.')

    token_info = json.loads(stdout)
    bearer_token = token_info['accessToken']
    return bearer_token
