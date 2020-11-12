# coding=utf-8

import requests


def get_access_token(service_principal_name, service_principal_password, tenant_id, resource_uri):
    url = "https://login.microsoftonline.com/{tenant_id}/oauth2/token".format(tenant_id=tenant_id)
    payload = {
        'grant_type': 'client_credentials',
        'client_id': service_principal_name,
        'client_secret': service_principal_password,
        'resource': resource_uri,
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    bearer_token = response.json()['access_token']
    return bearer_token
