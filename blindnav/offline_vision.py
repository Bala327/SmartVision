import subprocess
import os

DEMO_BIN = "/userdata/rknn_yolov5_demo"
MODEL = "/root/yolov5.rknn"
DEMO_DIR = "/userdata"
FRAME_PATH = "/tmp/nav_frame.jpg"

# Navigation-relevant COCO classes
HAZARD_PRIORITY = {
    'person': 'person',
    'car': 'car',
    'truck': 'truck',
    'bus': 'bus',
    'motorcycle': 'motorcycle',
    'bicycle': 'bicycle',
    'dog': 'dog',
    'cat': 'cat',
    'traffic light': 'traffic light',
    'stop sign': 'stop sign',
    'chair': 'obstacle',
    'bench': 'bench',
    'dining table': 'obstacle',
    'potted plant': 'obstacle',
    'fire hydrant': 'fire hydrant',
    'parking meter': 'pole',
    'suitcase': 'obstacle',
    'backpack': 'obstacle',
    'umbrella': 'obstacle',
    'bottle': 'obstacle',
}

def get_position(x1, x2, img_width=640):
    center = (x1 + x2) / 2
    if center < img_width * 0.35:
        return "on your left"
    elif center > img_width * 0.65:
        return "on your right"
    else:
        return "directly ahead"

def get_size(x1, y1, x2, y2, img_w=640, img_h=480):
    area = (x2 - x1) * (y2 - y1)
    total = img_w * img_h
    ratio = area / total
    if ratio > 0.3:
        return "very close"
    elif ratio > 0.1:
        return "nearby"
    else:
        return "ahead"

def analyze_offline(frame_path=FRAME_PATH):
    try:
        result = subprocess.run(
            [DEMO_BIN, MODEL, frame_path],
            capture_output=True,
            timeout=10,
            cwd=DEMO_DIR
        )
        output = result.stdout.decode('utf-8', errors='ignore')

        detections = []
        for line in output.splitlines():
            # Format: label @ (x1 y1 x2 y2) confidence
            if '@' in line and '(' in line:
                try:
                    parts = line.strip().split('@')
                    label = parts[0].strip()
                    coords_conf = parts[1].strip()
                    coords = coords_conf.split('(')[1].split(')')[0].split()
                    x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                    conf = float(coords_conf.split(')')[1].strip())

                    if label in HAZARD_PRIORITY and conf > 0.4:
                        name = HAZARD_PRIORITY[label]
                        position = get_position(x1, x2)
                        distance = get_size(x1, y1, x2, y2)
                        detections.append((conf, name, position, distance))
                except:
                    continue

        if not detections:
            return "Path appears clear. Proceed carefully."

        # Sort by confidence
        detections.sort(reverse=True)

        # Build instruction from top 2 detections
        instructions = []
        for conf, name, position, distance in detections[:2]:
            instructions.append(f"{name} {distance} {position}")

        result_text = ". ".join(instructions)

        # Add action based on most important detection
        top = detections[0]
        if top[2] == "directly ahead" and top[3] == "very close":
            result_text += ". Stop immediately."
        elif top[2] == "directly ahead":
            result_text += ". Slow down."
        else:
            result_text += ". Proceed with caution."

        return result_text

    except subprocess.TimeoutExpired:
        return "Offline analysis timed out. Proceed carefully."
    except Exception as e:
        print(f"[OFFLINE ERROR] {e}")
        return "Offline mode. Proceed carefully."
