import requests
import time

URL = 'http://127.0.0.1:8000/api/words/predict'
IMAGE_PATH = 'asl/but/00051.jpg'
SESSION_ID = 'testsession123'

with open(IMAGE_PATH, 'rb') as f:
    img = f.read()

for i in range(35):
    files = {'image': ('frame.jpg', img, 'image/jpeg')}
    data = {'session_id': SESSION_ID}
    try:
        r = requests.post(URL, files=files, data=data, timeout=10)
        print(i, 'status', r.status_code, r.json())
    except Exception as e:
        print(i, 'error', e)
    time.sleep(0.1)
