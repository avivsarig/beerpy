from fastapi import Request
import requests


def get_request(url: str, params: dict):
    return requests.get(url, params)

print(type(get_request))