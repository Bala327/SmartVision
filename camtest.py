import subprocess
import os
import base64
import struct
import tempfile

# video14 = ISP selfpath, fixed 576x324, NV12 format - ideal for Gemini
DEVICE   = "/dev/video14"
WIDTH    = 576
HEIGHT   = 324
FMT      = "NV12"
TMP_RAW  = "/tmp/nav_raw.yuv"
TMP_JPEG = "/tmp/nav_frame.jpg"

def _capture_nv12() -> bytes | None:
    """Capture one NV12 frame from ISP selfpath."""
    try:
        r = subprocess.run(
            [
                "v4l2-ctl", "-d", DEVICE,
                f"--set-fmt-video=width={WIDTH},height={HEIGHT},pixelformat={FMT}",
                "--stream-mmap", "--stream-count=1",
                f"--stream-to={TMP_RAW}",
            ],
            capture_output=True, timeout=5
        )
        if r.returncode == 0 and os.path.exists(TMP_RAW):
            with open(TMP_RAW, "rb") as f:
                data = f.read()
            os.remove(TMP_RAW)
            return data
    except Exception as e:
        print(f"[camera] capture error: {e}")
    return None


def _nv12_to_jpeg(nv12: bytes, quality: int = 70) -> bytes | None:
    """
    Convert NV12 bytes to JPEG using ffmpeg (hardware path via RV1106 RKMPP if available,
    falls back to software). ffmpeg is available on Buildroot via /usr/bin/ffmpeg.
    """
    try:
        # Write raw NV12 to temp file
        with open(TMP_RAW, "wb") as f:
            f.write(nv12)

        r = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-pix_fmt", "nv12",
                "-s", f"{WIDTH}x{HEIGHT}",
                "-i", TMP_RAW,
                "-q:v", str(quality),  # JPEG quality: 1=best, 31=worst; 5-10 is good
                TMP_JPEG,
            ],
            capture_output=True, timeout=5
        )
        if os.path.exists(TMP_JPEG):
            with open(TMP_JPEG, "rb") as f:
                data = f.read()
            os.remove(TMP_JPEG)
            return data
    except Exception as e:
        print(f"[camera] jpeg conversion error: {e}")
    return None


def _nv12_to_jpeg_pure(nv12: bytes, quality: int = 85) -> bytes | None:
    """
    Pure Python NV12JPEG fallback (no ffmpeg needed).
    Uses Python's struct + a minimal JPEG encoder approach via PIL if available.
    """
    try:
        from PIL import Image
        import io
        # NV12: Y plane (WxH) + interleaved UV plane (Wx H/2)
        y_size = WIDTH * HEIGHT
        y = nv12[:y_size]
        uv = nv12[y_size:]

        # Build RGB image from YUV
        import array
        rgb = bytearray(WIDTH * HEIGHT * 3)
        for row in range(HEIGHT):
            for col in range(WIDTH):
                yi = row * WIDTH + col
                uvi = (row // 2) * WIDTH + (col & ~1)
                Y  = nv12[yi]
                Cb = nv12[y_size + uvi] - 128
                Cr = nv12[y_size + uvi + 1] - 128
                r = max(0, min(255, int(Y + 1.402 * Cr)))
                g = max(0, min(255, int(Y - 0.344136 * Cb - 0.714136 * Cr)))
                b = max(0, min(255, int(Y + 1.772 * Cb)))
                base = yi * 3
                rgb[base] = r; rgb[base+1] = g; rgb[base+2] = b

        img = Image.frombytes("RGB", (WIDTH, HEIGHT), bytes(rgb))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    except Exception as e:
        print(f"[camera] pure fallback error: {e}")
    return None


def capture_frame_jpeg() -> bytes | None:
    """Main entry point - returns JPEG bytes ready for Gemini."""
    nv12 = _capture_nv12()
    if not nv12:
        return None

    # Try ffmpeg first (fast), fall back to pure Python
    jpeg = _nv12_to_jpeg(nv12)
    if not jpeg:
        print("[camera] ffmpeg failed, trying pure Python fallback...")
        jpeg = _nv12_to_jpeg_pure(nv12)
    return jpeg


def capture_frame_b64() -> str | None:
    """Returns base64-encoded JPEG for Gemini API."""
    raw = capture_frame_jpeg()
    if raw:
        return base64.b64encode(raw).decode("utf-8")
    return None


if __name__ == "__main__":
    print("[camera] Testing capture...")
    jpeg = capture_frame_jpeg()
    if jpeg:
        with open("/tmp/nav_test.jpg", "wb") as f:
            f.write(jpeg)
        print(f"[camera] ? JPEG saved: {len(jpeg)} bytes ({len(jpeg)//1024}KB)")
        print("[camera] Transfer /tmp/nav_test.jpg to your PC to verify the image")
    else:
        print("[camera] ? Capture failed")
