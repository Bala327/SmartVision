import urllib.request, json, ssl
from config import GEMINI_API_KEY

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}'
payload = json.dumps({'contents': [{'parts': [{'text': 'say hello'}]}]}).encode()
req = urllib.request.Request(url, data=payload, headers={'content-type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        data = json.loads(resp.read().decode())
        print(data['candidates'][0]['content']['parts'][0]['text'])
except urllib.error.HTTPError as e:
    print('Error', e.code, e.read().decode())
