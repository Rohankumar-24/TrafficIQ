import cv2
import pandas as pd
from ultralytics import YOLO
import supervision as sv
from datetime import datetime
import os

# ── LOAD MODEL ─────────────────────────────────────────
MODEL_PATH = "models/best (1).pt"
# MODEL_PATH = "D:\TrafficIQ-2\models\best.pt"
model = YOLO(MODEL_PATH if os.path.exists(MODEL_PATH) else "yolov8n.pt")

# ── PRINT YOUR ACTUAL CLASS IDs ────────────────────────
print("Your model classes:")
for id, name in model.model.names.items():
    print(f"  ID {id} = {name}")

# ── TRACKER ────────────────────────────────────────────
tracker = sv.ByteTrack(
    track_activation_threshold=0.25,
    lost_track_buffer=60,           # ✅ holds track longer
    minimum_matching_threshold=0.6, # ✅ less strict = more stable
    frame_rate=30
)

# ── ANNOTATORS ─────────────────────────────────────────
box_annotator   = sv.BoxAnnotator(thickness=2)
label_annotator = sv.LabelAnnotator(text_scale=0.55, text_thickness=1)

# ── VIDEO SOURCE SELECTION ─────────────────────────────
print("\nSelect source:")
print("1 - Video file")
print("2 - Webcam")
choice = input("Enter 1 or 2: ").strip()

if choice == "2":
    cap = cv2.VideoCapture(0)
    print("Using webcam...")
else:
    path = input("Enter video path (e.g. videos/traffic.mp4): ").strip()
    cap = cv2.VideoCapture(path)
    print(f"Using video: {path}")

# ── FRAME SIZE ─────────────────────────────────────────
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# ── STORAGE ────────────────────────────────────────────
records     = []
frame_count = 0
os.makedirs("data", exist_ok=True)

print("\nPress Q to quit and save data\n")

# ── MAIN LOOP ──────────────────────────────────────────
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Video ended or camera disconnected")
        break

    frame_count += 1
    frame = cv2.resize(frame, (1280, 720))

    # ── YOLO Detection ───────────────────────────────
    results = model(
        frame,
        conf=0.30,      # ✅ good balance
        iou=0.45,       # ✅ reduces duplicate boxes
        verbose=False
    )[0]

    detections = sv.Detections.from_ultralytics(results)

    # ── ✅ CORRECT FILTER — use YOUR model's class names ─
    # Only keep vehicle-type classes from your custom model
    VEHICLE_KEYWORDS = ["car", "bus", "truck", "motorbike",
                        "microbus", "pickup", "van", "vehicle"]

    if detections.class_id is not None and len(detections.class_id) > 0:
        keep = []
        for i, cls_id in enumerate(detections.class_id):
            cls_name = model.model.names[cls_id].lower()
            if any(kw in cls_name for kw in VEHICLE_KEYWORDS):
                keep.append(i)

        if keep:
            detections = detections[keep]
        else:
            # If no matches keep all — model is vehicle-only anyway
            pass

    # ── Tracking ─────────────────────────────────────
    detections = tracker.update_with_detections(detections)

    # ── Count and classify ───────────────────────────
    vehicle_count = len(detections)
    type_counts   = {}

    if detections.class_id is not None:
        for cls_id in detections.class_id:
            name = model.model.names[cls_id]
            type_counts[name] = type_counts.get(name, 0) + 1

    # ── Labels with tracking ID ──────────────────────
    labels = []
    if detections.tracker_id is not None:
        for i in range(len(detections)):
            cls_id = int(detections.class_id[i])
            conf   = float(detections.confidence[i])
            tid    = int(detections.tracker_id[i])
            name   = model.model.names[cls_id]
            labels.append(f"#{tid} {name} {conf:.0%}")
    else:
        for i in range(len(detections)):
            cls_id = int(detections.class_id[i])
            conf   = float(detections.confidence[i])
            name   = model.model.names[cls_id]
            labels.append(f"{name} {conf:.0%}")

    # ── Annotate frame ───────────────────────────────
    frame = box_annotator.annotate(scene=frame, detections=detections)
    frame = label_annotator.annotate(
        scene=frame, detections=detections, labels=labels
    )

    # ── Congestion level ─────────────────────────────
    def get_congestion(c):
        return "Low" if c <= 3 else "Medium" if c <= 8 else "High"

    congestion = get_congestion(vehicle_count)

    # ── On-screen stats ──────────────────────────────
    # Background panel
    cv2.rectangle(frame, (0, 0), (380, 110), (0, 0, 0), -1)

    cv2.putText(frame, f"Vehicles: {vehicle_count}",
                (12, 36), cv2.FONT_HERSHEY_SIMPLEX,
                1.1, (0, 255, 255), 2)

    cv2.putText(frame, f"Congestion: {congestion}",
                (12, 68), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (255, 255, 255), 2)

    types_str = "  ".join([f"{k}:{v}" for k, v in type_counts.items()])
    cv2.putText(frame, types_str if types_str else "Detecting...",
                (12, 98), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (180, 180, 180), 1)

    # ── Save record every 15 frames ──────────────────
    if frame_count % 15 == 0:
        records.append({
            "frame":           frame_count,
            "hour":            datetime.now().hour,
            "vehicle_count":   vehicle_count,
            "congestion":      congestion,
            "signal_duration": min(15 + vehicle_count * 4, 90),
            "types":           str(type_counts),
            "timestamp":       datetime.now().strftime("%H:%M:%S")
        })

        # Print live update every 15 frames
        print(f"Frame {frame_count:05d} | "
              f"Vehicles: {vehicle_count:2d} | "
              f"Congestion: {congestion:6s} | "
              f"{types_str}")

    cv2.imshow("TrafficIQ — Counter (Q to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ── CLEANUP ────────────────────────────────────────────
cap.release()
cv2.destroyAllWindows()

# ── SAVE CSV ───────────────────────────────────────────
df = pd.DataFrame(records)
df.to_csv("data/traffic_counts.csv", index=False)

print(f"\n✅ Saved {len(df)} records to data/traffic_counts.csv")
print(f"Total frames processed: {frame_count}")
if not df.empty:
    print("\nCongestion distribution:")
    print(df["congestion"].value_counts())
    print("\nSample data:")
    print(df.head())