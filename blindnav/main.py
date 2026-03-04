import time
from config import CAPTURE_INTERVAL
from camera import capture_jpeg_b64
from vision import analyze
from offline_vision import analyze_offline
from tts import speak, beep
from utils import check_internet
import base64

def save_frame(image_b64, path="/tmp/nav_frame.jpg"):
    with open(path, "wb") as f:
        f.write(base64.b64decode(image_b64))

def run():
    online = check_internet()
    speak("Navigation assistant starting.", online=online)
    speak("Ready. Scanning surroundings.", online=online)

    while True:
        try:
            online = check_internet()
            beep()

            image_b64 = capture_jpeg_b64()
            if image_b64 is None:
                speak("Camera error.", online=online)
                time.sleep(2)
                continue

            # Always save frame for offline use
            save_frame(image_b64)

            if online:
                instruction = analyze(image_b64)
                speak(instruction or "Could not read scene.", online=True)
            else:
                speak("Offline mode. Using local detection.", online=False)
                instruction = analyze_offline()
                speak(instruction, online=False)

            time.sleep(CAPTURE_INTERVAL)

        except KeyboardInterrupt:
            speak("Navigation stopped.", online=False)
            break
        except Exception as e:
            print(f"[MAIN ERROR] {e}")
            time.sleep(2)

if __name__ == "__main__":
    run()
