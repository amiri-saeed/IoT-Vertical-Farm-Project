import requests
import json


TELEGRAM_HOST = "http://127.0.0.1:8089"
payload = "message to user"
url = f"{TELEGRAM_HOST}/notify_user?room=1"
resp = requests.post(url, json=json.dumps(payload))
print(resp.json())
