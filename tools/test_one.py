import requests
URL = 'http://127.0.0.1:8000/api/words/predict'
IMAGE_PATH = 'asl/but/00051.jpg'
SESSION_ID = 'testsession123'
with open(IMAGE_PATH,'rb') as f:
    files = {'image': ('frame.jpg', f, 'image/jpeg')}
    data = {'session_id': SESSION_ID}
    r = requests.post(URL, files=files, data=data, timeout=10)
    print('status', r.status_code)
    print('text>', r.text[:2000])
