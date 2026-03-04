import urllib.request
import urllib.error
import json
import ssl
import time
from config import GEMINI_API_KEY, MAX_TOKENS

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

PROMPT = """You are a navigation assistant for a blind person walking outdoors.
Look at the image and respond in exactly 2 short sentences.
Sentence 1: Describe what obstacle or hazard you see and where it is (left, right, ahead).
Sentence 2: Give a clear action instruction (stop, move left, move right, walk ahead, slow down).
If path is clear just say: Path is clear, walk ahead safely.
Be specific: name the object (car, person, steps, pole, dog, wall, puddle etc).
Never say 'I see' or 'image shows'. Max 30 words total."""

def analyze(image_b64, retries=3, delay=15):
    for attempt in range(retries):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

            payload = json.dumps({
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_b64
                            }
                        },
                        {"text": PROMPT}
                    ]
                }],
                "generationConfig": {
                    "maxOutputTokens": MAX_TOKENS
                }
            }).encode('utf-8')

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"content-type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result['candidates'][0]['content']['parts'][0]['text'].strip()

        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"[VISION] Rate limit. Waiting {delay}s... (attempt {attempt+1}/{retries})")
                time.sleep(delay)
            else:
                print(f"[VISION] HTTP error: {e.code}")
                return None
        except urllib.error.URLError as e:
            print(f"[VISION] Network error: {e}")
            return None
        except Exception as e:
            print(f"[VISION ERROR] {e}")
            return None

    print("[VISION] All retries exhausted")
    return None
