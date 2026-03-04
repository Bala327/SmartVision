import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

from config import GEMINI_API_KEY
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}'
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
    data = json.loads(resp.read().decode())
    for m in data.get('models', []):
        if 'generateContent' in m.get('supportedGenerationMethods', []):
            print(m['name'])
