import subprocess
import base64
import os
import time

RTSP_URL = "rtsp://127.0.0.1:554/live/0"
CAPTURE_PATH = "/tmp/nav_frame.jpg"
STREAM_PID_FILE = "/tmp/cam_stream.pid"

def start_stream():
    """Start persistent ffmpeg stream that continuously overwrites the frame file."""
    # Kill any existing stream
    stop_stream()
    
    proc = subprocess.Popen([
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", RTSP_URL,
        "-vf", "fps=1",           # 1 frame per second
        "-q:v", "2",
        "-update", "1",           # keep overwriting same file
        "-y",
        CAPTURE_PATH
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Save PID
    with open(STREAM_PID_FILE, "w") as f:
        f.write(str(proc.pid))
    
    print(f"[CAM] Stream started PID {proc.pid}")
    # Wait for ISP to warm up
    time.sleep(4)
    return proc

def stop_stream():
    if os.path.exists(STREAM_PID_FILE):
        try:
            with open(STREAM_PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 9)
        except:
            pass
        os.remove(STREAM_PID_FILE)

def capture_jpeg_b64():
    """Read the latest frame from the persistent stream."""
    try:
        # Start stream if not running
        if not os.path.exists(STREAM_PID_FILE):
            start_stream()
        
        # Check if frame file exists and is fresh
        if not os.path.exists(CAPTURE_PATH):
            print("[CAM] No frame yet, waiting...")
            time.sleep(2)
        
        if not os.path.exists(CAPTURE_PATH):
            return None

        with open(CAPTURE_PATH, "rb") as f:
            data = f.read()

        if len(data) < 5000:
            print(f"[CAM] Frame too small: {len(data)} bytes")
            return None

        return base64.b64encode(data).decode("utf-8")

    except Exception as e:
        print(f"[CAM ERROR] {e}")
        return None
