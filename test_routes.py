import sys
import os

sys.path.append(os.path.dirname(__file__))
import app

client = app.app.test_client()

endpoints = [
    ('/', 'Module 6: Dashboard'),
    ('/data', 'Module 2: Data Table'),
    ('/datasets', 'Module 1: Dataset Collection & Management'),
    ('/statistics', 'Module 4: Statistics'),
    ('/visualization', 'Module 6: Visualization'),
    ('/crop-analysis', 'Module 5: Crop Yield Analysis'),
    ('/advisory', 'Module 7: Advisory Recommendation'),
    ('/about', 'About Project Page')
]

all_ok = True
for url, name in endpoints:
    resp = client.get(url)
    status = resp.status_code
    print(f"[{status}] {name} ({url})")
    if status != 200:
        all_ok = False

if all_ok:
    print("\nSUCCESS: All clean syllabus modules responded with HTTP 200 OK!")
else:
    print("\nWARNING: Some endpoints did not return 200.")
