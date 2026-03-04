import subprocess
import urllib.request
import urllib.parse
import ssl
import os

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

AUDIO_PATH = '/tmp/nav_speech.mp3'
PHRASES_DIR = '/userdata/phrases'

# Pre-cache these common phrases
COMMON_PHRASES = [
    "Navigation assistant starting.",
    "Ready. Scanning surroundings.",
    "Navigation stopped.",
    "Camera error.",
    "Offline mode.",
    "Path appears clear. Proceed carefully.",
    "Stop immediately.",
    "Slow down.",
    "Proceed with caution.",
    "Person directly ahead. Slow down.",
    "Person on your left. Proceed with caution.",
    "Person on your right. Proceed with caution.",
    "Car directly ahead. Stop immediately.",
    "Car nearby directly ahead. Slow down.",
    "Obstacle directly ahead. Slow down.",
    "Obstacle on your left. Proceed with caution.",
    "Obstacle on your right. Proceed with caution.",
]

def _phrase_file(text):
    safe = text.replace(' ', '_').replace('.', '').replace(',', '')[:40]
    return os.path.join(PHRASES_DIR, f"{safe}.mp3")

def cache_phrases():
    """Download and cache all common phrases via Google TTS."""
    os.makedirs(PHRASES_DIR, exist_ok=True)
    for phrase in COMMON_PHRASES:
        path = _phrase_file(phrase)
        if os.path.exists(path):
            continue
        try:
            encoded = urllib.parse.quote(phrase)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=en&client=tw-ob"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as resp:
                with open(path, 'wb') as f:
                    f.write(resp.read())
            print(f"[TTS] Cached: {phrase}")
        except Exception as e:
            print(f"[TTS] Failed to cache '{phrase}': {e}")

def _play_mp3(path):
    subprocess.run(
        f'ffmpeg -y -i {path} -f wav - 2>/dev/null | aplay -q',
        shell=True, timeout=30
    )

def speak(text, online=True):
    if not text:
        return
    print(f"[SPEAK] {text}")

    # Try cached phrase first
    cached = _phrase_file(text)
    if os.path.exists(cached):
        _play_mp3(cached)
        return

    # Try Google TTS if online
    if online:
        try:
            encoded = urllib.parse.quote(text)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=en&client=tw-ob"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8, context=SSL_CONTEXT) as resp:
                with open(AUDIO_PATH, 'wb') as f:
                    f.write(resp.read())
            _play_mp3(AUDIO_PATH)
            return
        except Exception as e:
            print(f"[TTS] Google TTS failed: {e}")

    # Offline fallback - find closest cached phrase
    text_lower = text.lower()
    for phrase in COMMON_PHRASES:
        for keyword in ['stop', 'clear', 'person', 'car', 'obstacle', 'slow', 'left', 'right', 'ahead']:
            if keyword in text_lower and keyword in phrase.lower():
                cached2 = _phrase_file(phrase)
                if os.path.exists(cached2):
                    print(f"[TTS] Using closest match: {phrase}")
                    _play_mp3(cached2)
                    return

    # Last resort - beep
    beep()

def beep():
    subprocess.run(
        'ffmpeg -y -f lavfi -i sine=frequency=800:duration=0.3 -f wav - 2>/dev/null | aplay -q',
        shell=True, timeout=5
    )
