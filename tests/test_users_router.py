from fastapi import Request
import requests

root = "http://127.0.0.1:8000"


def get_request(url: str):
    return requests.get(root + url).text


def test_root():
    assert get_request("/") == '{"detail":"Not Found"}'


def test_empty_users():
    assert get_request("/users") == '{"qty":0,"results":[]}'
