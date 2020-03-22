#!/usr/bin/env python3
import requests
import os

_PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY", "")
_PUSHOVER_API_TOKEN = os.environ.get("PUSHOVER_API_TOKEN", "")

def send(title, message, url=None):
    rsp = requests.post('https://api.pushover.net/1/messages.json', params={
        'token': _PUSHOVER_API_TOKEN,
        'user':  _PUSHOVER_USER_KEY,
        'title': title,
        'message': message,
        'sound': 'none',
        'url': url 
    })
    return rsp.json() if rsp.status_code < 300 else rsp.status_code

if __name__ == "__main__":
    import sys
    send(*sys.argv[1:])
