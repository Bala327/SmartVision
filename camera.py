import subprocess
import os
import base64

DEVICE   = "/dev/video14"
WIDTH    = 576
HEIGHT   = 324
FMT      = "NV12"
TMP_RAW  = "/tmp/nav_raw.yuv"
TMP_JPEG = "/tmp/nav_frame.jpg"

def _capture_nv12():
    try:
        r = subprocess.run(
            ["v4l2-ctl", "-d", DEVICE,
             "--set-fmt-video=width=" + str(WIDTH) + ",height=" + str(HEIGHT) + ",pixelformat=" + FMT,
             "--stream-mmap", "--stream-count=1",
             "--stream-to=" + TMP_RAW],
            capture_output=True, timeout=5
        )
        if r.returncode == 0 and os.path.exists(TMP_RAW):
            with open(TMP_RAW, "rb") as f:
                data = f.read()
            os.remove(TMP_RAW)
            return data
    except Exception as e:
        print("[camera] capture error: " + str(e))
    return None

def _nv12_to_jpeg(nv12):
    try:
        with open(TMP_RAW, "wb") as f:
            f.write(nv12)
        r = subprocess.run(
            ["ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "nv12",
             "-s", str(WIDTH) + "x" + str(HEIGHT),
             "-i", TMP_RAW, "-q:v", "5", TMP_JPEG],
            capture_output=True, timeout=5
        )
        if os.path.exists(TMP_JPEG):
            with open(TMP_JPEG, "rb") as f:
                data = f.read()
            os.remove(TMP_JPEG)
            return data
    except Exception as e:
        print("[camera] jpeg error: " + str(e))
    return None

def capture_frame_jpeg():
    nv12 = _capture_nv12()
    if not nv12:
        return None
    return _nv12_to_jpeg(nv12)

def capture_frame_b64():
    raw = capture_frame_jpeg()
    if raw:
        return base64.b64encode(raw).decode("utf-8")
    return None
