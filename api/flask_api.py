from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import cv2
import joblib
import pandas as pd
import time
import threading
import base64
import os
import csv
from datetime import datetime
from ultralytics import YOLO

app = Flask(__name__)
CORS(app, origins="*")

# ── Load models ───────────────────────────────────────────
print("Loading models...")
yolo    = YOLO("models/best.pt")
clf     = joblib.load("models/classifier.pkl")
reg     = joblib.load("models/regressor.pkl")
le_lane = joblib.load("models/le_lane.pkl")
le_cong = joblib.load("models/le_congestion.pkl")
print("✅ Models loaded:", yolo.model.names)

# ── Emergency class IDs ───────────────────────────────────
EMERGENCY_IDS = [
    cid for cid, name in yolo.model.names.items()
    if "ambulance" in name.lower()
]
print(f"✅ Emergency class IDs: {EMERGENCY_IDS}")
print(f"✅ Emergency classes  : {[yolo.model.names[i] for i in EMERGENCY_IDS]}")

# ── Global state ──────────────────────────────────────────
state = {
    "running":    False,
    "green_lane": "lane2",
    "session_id": None,
    "lane1": {
        "count": 0, "congestion": "Low",
        "signal": "red", "duration": 0,
        "emergency": False, "types": {},
        "frame_b64": None
    },
    "lane2": {
        "count": 0, "congestion": "Low",
        "signal": "green", "duration": 0,
        "emergency": False, "types": {},
        "frame_b64": None
    }
}

session_logs = []
all_sessions = []
stop_event   = threading.Event()

# ── Helpers ───────────────────────────────────────────────
def predict_signal(count, hour, lane):
    try:
        enc = le_lane.transform([lane])[0]
    except:
        enc = 0
    X    = pd.DataFrame(
        [[count, hour, enc]],
        columns=["vehicle_count", "hour", "lane_encoded"]
    )
    cong = le_cong.inverse_transform(clf.predict(X))[0]
    dur  = int(reg.predict(X)[0])
    return cong, min(dur, 120)

def frame_to_b64(frame):
    _, buf = cv2.imencode(
        '.jpg', frame,
        [cv2.IMWRITE_JPEG_QUALITY, 75]
    )
    return base64.b64encode(buf).decode('utf-8')

def process_frame(frame):
    # ✅ Bigger frame = clearer detection
    frame   = cv2.resize(frame, (720, 405))
    h, w    = frame.shape[:2]

    results = yolo.track(
        frame,
        conf    = 0.20,
        iou     = 0.35,
        imgsz   = 640,
        persist = True,
        tracker = "bytetrack.yaml",
        verbose = False
    )[0]

    count  = 0
    emerg  = False
    types  = {}

    if results.boxes is not None:
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id   = int(box.cls[0])
            cls_name = yolo.model.names[cls_id]
            conf_val = float(box.conf[0])

            # Count vehicles
            types[cls_name] = types.get(cls_name, 0) + 1
            count += 1

            # Emergency check
            is_emerg = cls_id in EMERGENCY_IDS
            if is_emerg:
                emerg = True
                color = (0, 60, 255)    # red for emergency
            else:
                color = (0, 220, 80)    # green for normal

            # ✅ Draw bounding box
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

            # ✅ Draw label with confidence
            lbl  = "EMERGENCY" if is_emerg else cls_name.upper()
            lbl  = f"{lbl} {conf_val:.0%}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.5
            thick = 1

            (lw, lh), bl = cv2.getTextSize(lbl, font, scale, thick)
            cv2.rectangle(frame,
                          (x1, y1 - lh - bl - 5),
                          (x1 + lw + 6, y1),
                          color, -1)
            cv2.putText(frame, lbl,
                        (x1 + 3, y1 - bl - 2),
                        font, scale, (0, 0, 0), thick)

    # ✅ Top-left overlay — vehicle count
    # cv2.rectangle(frame, (0, 0), (230, 55), (8, 10, 18), -1)
    # cv2.putText(frame,
    #             f"VEHICLES: {count}",
    #             (8, 36),
    #             cv2.FONT_HERSHEY_SIMPLEX,
    #             0.75, (255, 255, 255), 2)

    # ✅ Bottom emergency bar
    if emerg:
        cv2.rectangle(frame, (0, h-30), (w, h), (100, 0, 0), -1)
        cv2.putText(frame,
                    "EMERGENCY VEHICLE DETECTED",
                    (8, h-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (255, 80, 80), 1)

    return frame, count, emerg, types

# ── Detection loop ────────────────────────────────────────
def detection_loop(v1_path, v2_path, hour):
    global state, session_logs

    cap1 = cv2.VideoCapture(v1_path) if v1_path else None
    cap2 = cv2.VideoCapture(v2_path) if v2_path else None

    # ✅ Emergency hold tracking
    last_e1 = last_e2 = 0.0
    HOLD    = 5  # seconds to hold emergency state

    state["running"]    = True
    state["session_id"] = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_logs.clear()

    frame_n = 0
    cong_counts = {"Low": 0, "Medium": 0, "High": 0}
    all_types   = {}

    while not stop_event.is_set():
        frame_n += 1
        f1 = f2 = None

        # ✅ Read with loop support
        if cap1 and cap1.isOpened():
            ret, f1 = cap1.read()
            if not ret:
                cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, f1 = cap1.read()

        if cap2 and cap2.isOpened():
            ret, f2 = cap2.read()
            if not ret:
                cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, f2 = cap2.read()

        cnt1 = cnt2 = 0
        raw_e1 = raw_e2 = False
        t1 = t2 = {}

        if f1 is not None:
            f1, cnt1, raw_e1, t1 = process_frame(f1)
        if f2 is not None:
            f2, cnt2, raw_e2, t2 = process_frame(f2)

        # ✅ Emergency hold logic
        now = time.time()
        if raw_e1: last_e1 = now
        if raw_e2: last_e2 = now
        e1 = (now - last_e1) < HOLD
        e2 = (now - last_e2) < HOLD

        # ✅ Signal decision
        cong1, dur1 = predict_signal(cnt1, hour, "North")
        cong2, dur2 = predict_signal(cnt2, hour, "South")

        if e1 and not e2:
            sig1, sig2 = "green", "red"
            d1, d2     = 20, 25
            gl         = "lane1"
        elif e2 and not e1:
            sig1, sig2 = "red", "green"
            d1, d2     = 25, 20
            gl         = "lane2"
        elif cnt1 >= cnt2:
            sig1, sig2 = "green", "red"
            d1, d2     = dur1, dur1 + 3
            gl         = "lane1"
        else:
            sig1, sig2 = "red", "green"
            d1, d2     = dur2 + 3, dur2
            gl         = "lane2"

        # ✅ Update state
        state["lane1"] = {
            "count":      cnt1,
            "congestion": "EMERGENCY" if e1 else cong1,
            "signal":     sig1,
            "duration":   d1,
            "emergency":  e1,
            "types":      t1,
            "frame_b64":  frame_to_b64(f1) if f1 is not None else None
        }
        state["lane2"] = {
            "count":      cnt2,
            "congestion": "EMERGENCY" if e2 else cong2,
            "signal":     sig2,
            "duration":   d2,
            "emergency":  e2,
            "types":      t2,
            "frame_b64":  frame_to_b64(f2) if f2 is not None else None
        }
        state["green_lane"] = gl

        # ✅ Track congestion for real analytics
        if cong1 in cong_counts: cong_counts[cong1] += 1
        if cong2 in cong_counts: cong_counts[cong2] += 1

        # ✅ Track vehicle types for real analytics
        for k, v in t1.items():
            all_types[k] = all_types.get(k, 0) + v
        for k, v in t2.items():
            all_types[k] = all_types.get(k, 0) + v

        # ✅ Save log every 30 frames
        if frame_n % 30 == 0:
            session_logs.append({
                "timestamp":        datetime.now().strftime("%H:%M:%S"),
                "lane1_count":      cnt1,
                "lane2_count":      cnt2,
                "lane1_congestion": "EMERGENCY" if e1 else cong1,
                "lane2_congestion": "EMERGENCY" if e2 else cong2,
                "green_lane":       gl,
                "emergency":        e1 or e2
            })

        time.sleep(0.05)

    # ✅ Save completed session to history
    if session_logs:
        l1_counts = [l["lane1_count"] for l in session_logs]
        l2_counts = [l["lane2_count"] for l in session_logs]

        all_sessions.append({
            "session_id":    state["session_id"],
            "start_time":    state["session_id"],
            "total_frames":  frame_n,
            "avg_l1":        round(sum(l1_counts)/len(l1_counts), 1),
            "avg_l2":        round(sum(l2_counts)/len(l2_counts), 1),
            "emergencies":   sum(1 for l in session_logs if l["emergency"]),
            "peak_cong_l1":  max(set([l["lane1_congestion"]
                                      for l in session_logs]),
                                 key=["Low","Medium","High","EMERGENCY"].index
                                 if False else lambda x:
                                 ["Low","Medium","High","EMERGENCY"].index(x)
                                 if x in ["Low","Medium","High","EMERGENCY"]
                                 else 0),
            "cong_counts":   cong_counts,
            "vehicle_types": all_types,
            "logs":          session_logs.copy()
        })

    state["running"] = False
    if cap1: cap1.release()
    if cap2: cap2.release()
    print(f"✅ Session saved: {state['session_id']}")

# ── API ROUTES ────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    return jsonify({
        "status":  "online",
        "running": state["running"],
        "classes": yolo.model.names,
        "emergency_classes": [yolo.model.names[i] for i in EMERGENCY_IDS]
    })

@app.route("/api/start", methods=["POST"])
def api_start():
    global stop_event

    if state["running"]:
        stop_event.set()
        time.sleep(1.5)

    data = request.json or {}
    v1   = data.get("video1", "")
    v2   = data.get("video2", "")
    hour = int(data.get("hour", 8))

    stop_event.clear()
    t = threading.Thread(
        target = detection_loop,
        args   = (v1, v2, hour),
        daemon = True
    )
    t.start()

    return jsonify({
        "message": "Detection started",
        "session": datetime.now().strftime("%Y%m%d_%H%M%S")
    })

@app.route("/api/stop", methods=["POST"])
def api_stop():
    stop_event.set()
    return jsonify({"message": "Detection stopped"})

@app.route("/api/data")
def api_data():
    return jsonify({
        "running":    state["running"],
        "green_lane": state["green_lane"],
        "lane1": {
            k: v for k, v in state["lane1"].items()
            if k != "frame_b64"
        },
        "lane2": {
            k: v for k, v in state["lane2"].items()
            if k != "frame_b64"
        }
    })

@app.route("/api/frame/<int:lane>")
def api_frame(lane):
    key = f"lane{lane}"
    b64 = state.get(key, {}).get("frame_b64")
    return jsonify({"frame": b64})

@app.route("/api/analytics")
def api_analytics():
    if not session_logs:
        return jsonify({
            "timeline":       [],
            "congestion_dist": {"Low": 0, "Medium": 0, "High": 0},
            "vehicle_types":   {},
            "emergency_count": 0,
            "avg_lane1":       0,
            "avg_lane2":       0
        })

    # ✅ Real analytics from actual session data
    l1 = [l["lane1_count"] for l in session_logs]
    l2 = [l["lane2_count"] for l in session_logs]

    cong_dist = {"Low": 0, "Medium": 0, "High": 0}
    all_types = {}

    for log in session_logs:
        c = log.get("lane1_congestion", "Low")
        if c in cong_dist:
            cong_dist[c] += 1

    # Get vehicle types from current state
    for k, v in state["lane1"].get("types", {}).items():
        all_types[k] = all_types.get(k, 0) + v
    for k, v in state["lane2"].get("types", {}).items():
        all_types[k] = all_types.get(k, 0) + v

    return jsonify({
        "timeline":        session_logs[-60:],
        "congestion_dist": cong_dist,
        "vehicle_types":   all_types,
        "emergency_count": sum(1 for l in session_logs if l["emergency"]),
        "avg_lane1":       round(sum(l1)/len(l1), 1) if l1 else 0,
        "avg_lane2":       round(sum(l2)/len(l2), 1) if l2 else 0
    })

@app.route("/api/history")
def api_history():
    return jsonify({
        "sessions": [
            {k: v for k, v in s.items() if k != "logs"}
            for s in all_sessions
        ],
        "total": len(all_sessions)
    })

@app.route("/api/history/<session_id>")
def api_history_detail(session_id):
    for s in all_sessions:
        if s["session_id"] == session_id:
            return jsonify(s)
    return jsonify({"error": "Session not found"}), 404

@app.route("/api/upload", methods=["POST"])
def api_upload():
    os.makedirs("videos", exist_ok=True)
    paths = {}

    for key in ["video1", "video2"]:
        if key in request.files:
            f    = request.files[key]
            path = f"videos/{key}_{int(time.time())}.mp4"
            f.save(path)
            paths[key] = os.path.abspath(path)
            print(f"✅ Saved {key} to {paths[key]}")

    if paths:
        return jsonify(paths)

    return jsonify({"error": "No file uploaded"}), 400

@app.route("/api/export/csv")
def api_export():
    if not session_logs:
        return jsonify({"error": "No session data to export"}), 400

    os.makedirs("data", exist_ok=True)
    path = "data/session_export.csv"

    with open(path, "w", newline="") as f:
        fields = ["timestamp", "lane1_count", "lane2_count",
                  "lane1_congestion", "lane2_congestion",
                  "green_lane", "emergency"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(session_logs)

    return send_file(
        os.path.abspath(path),
        as_attachment=True,
        download_name="trafficiq_session.csv"
    )

# ── Run ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚦 TrafficIQ Flask API")
    print("📡 http://localhost:5001")
    print("\nEndpoints:")
    print("  GET  /api/status")
    print("  POST /api/start   body: {video1, video2, hour}")
    print("  POST /api/stop")
    print("  GET  /api/data")
    print("  GET  /api/frame/1")
    print("  GET  /api/frame/2")
    print("  GET  /api/analytics")
    print("  GET  /api/history")
    print("  GET  /api/history/<session_id>")
    print("  POST /api/upload")
    print("  GET  /api/export/csv\n")
    app.run(port=5001, threaded=True, debug=False)