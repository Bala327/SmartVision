import asyncio
import base64
import json
import os
import sys
import struct
import subprocess
import threading
import queue

sys.path.insert(0, '/project')
import camera

API_KEY        = os.environ.get("GOOGLE_API_KEY", "AIzaSyCIVSNOmVu4XcBE376VMtnXOqgiQsdJivw")
MODEL          = "gemini-2.0-flash-live-001"
HOST           = "generativelanguage.googleapis.com"
URI            = "wss://" + HOST + "/ws/google.ai.generativelanguage.v1beta.BidiGenerateContent?key=" + API_KEY
FRAME_INTERVAL = 2.0

SYSTEM_PROMPT = (
    "You are a real-time navigation assistant for a visually impaired person. "
    "You receive images from a forward-facing camera. "
    "Describe obstacles and path in MAX 2 short sentences. "
    "Lead with the most urgent hazard first. "
    "Use words: ahead, left, right, stop, step up, step down. "
    "If path is clear say: Path is clear, continue forward. "
    "Never describe irrelevant background details. Speak calmly."
)

DEVICE_RATE  = 22050
GEMINI_RATE  = 24000
CHANNELS     = 2
_audio_queue = queue.Queue()

def _resample(pcm_24k_mono):
    samples = struct.unpack(str(len(pcm_24k_mono)//2) + 'h', pcm_24k_mono)
    ratio   = GEMINI_RATE / DEVICE_RATE
    out_len = int(len(samples) / ratio)
    out     = []
    for i in range(out_len):
        src  = i * ratio
        idx  = int(src)
        frac = src - idx
        s0   = samples[idx]
        s1   = samples[idx+1] if idx+1 < len(samples) else s0
        s    = int(s0 + frac*(s1-s0))
        out.extend([s, s])
    return struct.pack(str(len(out)) + 'h', *out)

def _play_raw(pcm):
    proc = subprocess.Popen(
        ["aplay", "-D", "plug:hw:0,0", "-f", "S16_LE",
         "-r", str(DEVICE_RATE), "-c", str(CHANNELS), "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proc.communicate(input=pcm)

def _audio_worker():
    buf        = b""
    FLUSH_SIZE = DEVICE_RATE * 2 * CHANNELS
    while True:
        try:
            chunk = _audio_queue.get(timeout=0.5)
            if chunk is None:
                break
            buf += _resample(chunk)
            if len(buf) >= FLUSH_SIZE:
                _play_raw(buf)
                buf = b""
        except queue.Empty:
            if buf:
                _play_raw(buf)
                buf = b""

def start_audio():
    t = threading.Thread(target=_audio_worker, daemon=True)
    t.start()
    return t

async def run():
    import websockets

    print("[nav] Connecting to Gemini Live...")

    uri = "wss://" + HOST + "/ws/google.ai.generativelanguage.v1beta.BidiGenerateContent?key=" + API_KEY

    async with websockets.connect(
        uri,
        additional_headers={"Content-Type": "application/json"},
        max_size=10 * 1024 * 1024,
        ping_interval=20,
        ping_timeout=10,
    ) as ws:

        setup = {
            "setup": {
                "model": "models/" + MODEL,
                "generation_config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {
                                "voice_name": "Aoede"
                            }
                        }
                    }
                },
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                }
            }
        }
        await ws.send(json.dumps(setup))
        resp = await ws.recv()
        print("[nav] Setup: " + str(resp[:80]))
        print("[nav] Connected! Navigation starting...")

        async def send_frames():
            import time
            while True:
                t0 = time.monotonic()
                frame_b64 = camera.capture_frame_b64()
                if frame_b64:
                    msg = {
                        "realtimeInput": {
                            "mediaChunks": [{
                                "mimeType": "image/jpeg",
                                "data": frame_b64
                            }]
                        }
                    }
                    await ws.send(json.dumps(msg))
                    print("[nav] Frame sent")
                else:
                    print("[nav] Frame capture failed")
                elapsed = time.monotonic() - t0
                await asyncio.sleep(max(0, FRAME_INTERVAL - elapsed))

        async def receive_audio():
            async for message in ws:
                try:
                    data  = json.loads(message)
                    parts = (data
                             .get("serverContent", {})
                             .get("modelTurn", {})
                             .get("parts", []))
                    for part in parts:
                        if "inlineData" in part:
                            pcm = base64.b64decode(part["inlineData"]["data"])
                            _audio_queue.put(pcm)
                            print("[nav] Audio: " + str(len(pcm)) + " bytes")
                        elif "text" in part:
                            print("[gemini] " + part["text"])
                except Exception as e:
                    print("[nav] Parse error: " + str(e))

        await asyncio.gather(send_frames(), receive_audio())

async def main():
    while True:
        try:
            await run()
        except Exception as e:
            print("[nav] Error: " + str(e) + ". Reconnecting in 3s...")
            await asyncio.sleep(3)

if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: GOOGLE_API_KEY not set. Run: export GOOGLE_API_KEY=your_key")
        sys.exit(1)
    start_audio()
    print("[nav] Audio started")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[nav] Stopped.")
        _audio_queue.put(None)


