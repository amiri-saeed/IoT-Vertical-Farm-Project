import requests
import io
import base64
import json
from PIL import Image


base = "http://127.0.0.1:8085"
# headers = {'Content-type': 'application/json'}

url = f"{base}/plot?room=1&tower=2&shelf=1&sensor=height&start=2001-02-02 12:00:15"
req = requests.get(url).json()

file_to_write = open("plot_base64.json", 'w')
json.dump(req, file_to_write)
print(req)

# bs4_img = req["bs4_img"]
# img = Image.open(io.BytesIO(base64.decodebytes(bytes(bs4_img, "utf-8"))))
# img.save("plot.jpg")



# url = f"{base}/average?room=1&tower=2&shelf=1&sensor=temp&start=2001-02-02 12:00:15"
# req = requests.get(url).json()
# print(req)



# url = f"{base}/max?room=1&tower=2&shelf=1&sensor=temp&start=2001-02-02 12:00:15"
# req = requests.get(url).json()
# print(req)



# url = f"{base}/min?room=1&tower=2&shelf=1&sensor=temp&start=2001-02-02 12:00:15"
# req = requests.get(url).json()
# print(req)


# url = f"{base}/plot_compare_shelf?room=1&tower=2&shelf=1&sensor=height,li,moisture"
# req = requests.get(url).json()
# print(req)

# bs4_img = req["bs4_img"]
# img = Image.open(io.BytesIO(base64.decodebytes(bytes(bs4_img, "utf-8"))))
# img.save("plot_compare_shelf.jpg")



# url = f"{base}/plot_compare_shelves?room=1&sensor=ph"
# req = requests.get(url).json()
# print(req)

# bs4_img = req["bs4_img"]
# img = Image.open(io.BytesIO(base64.decodebytes(bytes(bs4_img, "utf-8"))))
# img.save("plot_compare_shelves.jpg")

