from fastapi import Request
import requests


<<<<<<< HEAD
def get_request(url: str, params: dict):
    return requests.get(url, params)

print(type(get_request))
=======
def check_get_user(request: Request) -> dict:
    return requests.get(request)
>>>>>>> 7c5462f (tests dir added)
