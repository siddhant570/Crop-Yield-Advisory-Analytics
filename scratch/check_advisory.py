import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import app
import re

client = app.app.test_client()
r = client.get('/advisory')
html = r.data.decode('utf-8', errors='ignore')

matches = re.findall(r'Yield Projection.*?([0-9.]+)\s*<span', html, re.DOTALL)
print('Yield Projection:', matches)
baseline = re.findall(r'Hist\. Baseline:\s*([0-9.]+)', html)
print('Hist Baseline:', baseline)
health = re.findall(r'Health Index.*?([0-9]+)/100', html, re.DOTALL)
print('Health Score:', health)
selected_options = re.findall(r'<option value="([^"]+)"\s*selected', html)
print('Selected options:', selected_options)
