from fastapi import Request
import requests


def check_get_user(request: Request) -> dict:
    return requests.get(request)
