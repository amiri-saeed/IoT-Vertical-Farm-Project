import requests
import time
from pprint import pprint as pp


base = "http://127.0.0.1:8086/"
print(requests.get(base).status_code)

# url = f"{base}/retrieve?room=1&tower=1&shelf=1&sensor=li"
# req = requests.get(url).json()
# print("bsae request, default optionals: ", req)
# time.sleep(3)

# url = f"{base}/retrieve?room=1&tower=1&shelf=1&sensor=ph&last=3"
# req = requests.get(url).json()
# print("last 3 results: ", req)
# time.sleep(4)

# url = f"{base}/retrieve?room=1&tower=1&shelf=1&sensor=temp&start=2024-03-21 15:00:00"
# req = requests.get(url).json()
# print("strting time after some arbitrary time: ", req)
# time.sleep(3)


# url = f"{base}/clear?room=1&shelf=1&tower=1"
# print(requests.delete(url).json())
# time.sleep(5)

# url = f"{base}/clear?room=1"
# print(requests.delete(url).json())
# time.sleep(4)

# url = f"{base}/clear?room=1&shelf=2"
# print(requests.delete(url).json())