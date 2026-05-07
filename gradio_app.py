import gradio as gr
import cv2
import joblib
import pandas as pd
import numpy as np
import time
from ultralytics import YOLO

# ── LOAD MODELS ──────────────────────────────────────────
def load_models():
    yolo    = YOLO("models/best.pt")
    # yolo    = YOLO("best.pt")
    clf     = joblib.load("models/classifier.pkl")
    reg     = joblib.load("models/regressor.pkl")
    le_lane = joblib.load("models/le_lane.pkl")
    le_cong = joblib.load("models/le_congestion.pkl")
    print("✅ Models loaded")
    print("Classes:", yolo.model.names)
    return yolo, clf, reg, le_lane, le_cong

yolo, clf, reg, le_lane, le_cong = load_models()

# ── EMERGENCY SETUP ───────────────────────────────────────
# Auto-detect emergency class IDs from model
EMERGENCY_CLASS_IDS = []

def setup_emergency_ids():
    global EMERGENCY_CLASS_IDS
    keywords = ["ambulance", "fire", "police", "emergency", "paramedic"]
    for cls_id, cls_name in yolo.model.names.items():
        if any(k in cls_name.lower() for k in keywords):
            EMERGENCY_CLASS_IDS.append(cls_id)
            print(f"✅ Emergency class: ID={cls_id}  Name={cls_name}")
    if not EMERGENCY_CLASS_IDS:
        print("⚠️ No emergency classes found in model!")
        print("   Available classes:", yolo.model.names)

setup_emergency_ids()

# ── CONSTANTS ─────────────────────────────────────────────
EMERGENCY_GREEN_TIME   = 20
EMERGENCY_RED_TIME     = 25
EMERGENCY_HOLD_SECONDS = 5
YELLOW_DURATION        = 3

# ── HELPERS ───────────────────────────────────────────────
def predict_signal(count, hour, lane):
    try:
        lane_enc = le_lane.transform([lane])[0]
    except:
        lane_enc = 0
    X = pd.DataFrame(
        [[count, hour, lane_enc]],
        columns=["vehicle_count", "hour", "lane_encoded"]
    )
    cong = le_cong.inverse_transform(clf.predict(X))[0]
    dur  = int(reg.predict(X)[0])
    return cong, min(dur, 120)

def is_emergency(cls_id, cls_name):
    # ✅ Check by class ID — most reliable method
    if cls_id in EMERGENCY_CLASS_IDS:
        return True
    # ✅ Fallback — check by name
    keywords = ["ambulance", "fire", "police", "emergency", "paramedic"]
    return any(k in cls_name.lower() for k in keywords)

# ── PROCESS FRAME ─────────────────────────────────────────
def process_frame(frame, lane_name, lane_num):
    frame = cv2.resize(frame, (720, 405))
    h, w  = frame.shape[:2]

    results = yolo.track(
        frame,
        # conf    = 0.25,
        # iou     = 0.45,
        conf    = 0.15,
        iou     = 0.35,
        imgsz   = 640,
        persist = True,
        tracker = "bytetrack.yaml",
        verbose = False
    )[0]

    tracked_ids = set()
    fallback    = 0
    has_emerg   = False
    type_counts = {}

    if results.boxes is not None:
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id   = int(box.cls[0])
            cls_name = yolo.model.names[cls_id]
            conf_val = float(box.conf[0])

            type_counts[cls_name] = type_counts.get(cls_name, 0) + 1

            tid = None
            if box.id is not None:
                try:
                    tid = int(box.id[0])
                    tracked_ids.add(tid)
                except:
                    pass
            fallback += 1

            # ✅ Pass both cls_id AND cls_name
            emerg = is_emergency(cls_id, cls_name)

            if emerg:
                has_emerg = True
                color = (0, 60, 255)    # red box
                print(f"🚨 Emergency detected: {cls_name} (ID:{cls_id}) conf:{conf_val:.2f}")
            else:
                color = (0, 220, 80)    # green box

            # Detection box
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

            # Label
            lbl = "EMERGENCY" if emerg else cls_name.upper()
            (lw, lh), bl = cv2.getTextSize(
                lbl, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
            )
            cv2.rectangle(frame,
                          (x1, y1-lh-bl-4),
                          (x1+lw+6, y1),
                          color, -1)
            cv2.putText(frame, lbl,
                        (x1+3, y1-bl-2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (0,0,0), 1)

    count = len(tracked_ids) if tracked_ids else fallback

    # Minimal overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (210,50), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    cv2.putText(frame,
                f"LANE {lane_num}  |  {lane_name.upper()}",
                (8,16), cv2.FONT_HERSHEY_SIMPLEX,
                0.4, (80,200,255), 1)
    cv2.putText(frame,
                f"VEHICLES: {count}",
                (8,38), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (255,255,255), 1)

    if has_emerg:
        cv2.rectangle(frame, (0,h-26), (w,h), (120,0,0), -1)
        cv2.putText(frame, "EMERGENCY DETECTED",
                    (8,h-9), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (255,80,80), 1)

    return frame, count, has_emerg, type_counts

# ── SIGNAL LOGIC ──────────────────────────────────────────
def compute_signals(cnt1, cnt2, dur1, dur2, e1, e2):
    if e1 and not e2:
        return (EMERGENCY_GREEN_TIME, 0, 0, True,
                0, 0, EMERGENCY_RED_TIME, False)
    elif e2 and not e1:
        return (0, 0, EMERGENCY_RED_TIME, False,
                EMERGENCY_GREEN_TIME, 0, 0, True)
    elif cnt1 >= cnt2:
        return (dur1, YELLOW_DURATION, 0, False,
                0, 0, dur1+YELLOW_DURATION, False)
    else:
        return (0, 0, dur2+YELLOW_DURATION, False,
                dur2, YELLOW_DURATION, 0, False)

# ── BUILD INFO TEXT ───────────────────────────────────────
def build_info(lane_name, count, cong, types_dict,
               green, yellow, red, emerg_active, is_lane_emerg):

    types_str = "  |  ".join(
        [f"{k}: {v}" for k, v in sorted(types_dict.items())]
    ) if types_dict else "detecting..."

    if is_lane_emerg:
        signal_line = f"🚨 EMERGENCY GREEN: {green}s   🟡 0s   🔴 0s"
    else:
        g = f"🟢 Green: {green}s"   if green  > 0 else "🟢 0s"
        y = f"🟡 Yellow: {yellow}s" if yellow > 0 else "🟡 0s"
        r = f"🔴 Red: {red}s"       if red    > 0 else "🔴 0s"
        signal_line = f"{g}   {y}   {r}"

    emerg_line = "YES 🚨" if emerg_active else "NO"

    return f"""
📍  {lane_name}
{'─' * 32}
🚗  Vehicles      :  {count}
🚦  Signal        :  {signal_line}
📊  Congestion    :  {cong}
🚑  Emergency     :  {emerg_line}
🔍  Types         :  {types_str}
"""

# ── EMERGENCY STATE ───────────────────────────────────────
last_e1 = [0.0]
last_e2 = [0.0]

# ── MAIN DETECT FUNCTION ──────────────────────────────────
def detect(video1_path, video2_path,
           lane1_name, lane2_name,
           hour, frame_skip):

    if not video1_path and not video2_path:
        yield (None, None,
               "❌ Please upload at least one video",
               "❌ Please upload at least one video")
        return

    cap1 = cv2.VideoCapture(video1_path) if video1_path else None
    cap2 = cv2.VideoCapture(video2_path) if video2_path else None

    last_e1[0] = last_e2[0] = 0.0
    frame_count = 0

    while True:
        frame_count += 1
        f1 = f2 = None

        if cap1 and cap1.isOpened():
            ret1, f1 = cap1.read()
            if not ret1:
                cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
                _, f1 = cap1.read()

        if cap2 and cap2.isOpened():
            ret2, f2 = cap2.read()
            if not ret2:
                cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
                _, f2 = cap2.read()

        if frame_count % int(frame_skip) != 0:
            time.sleep(0.005)
            continue

        cnt1 = cnt2 = 0
        re1  = re2  = False
        t1d  = t2d  = {}
        out1 = out2 = None

        if f1 is not None:
            f1, cnt1, re1, t1d = process_frame(f1, lane1_name, 1)
            out1 = cv2.cvtColor(f1, cv2.COLOR_BGR2RGB)

        if f2 is not None:
            f2, cnt2, re2, t2d = process_frame(f2, lane2_name, 2)
            out2 = cv2.cvtColor(f2, cv2.COLOR_BGR2RGB)

        now = time.time()
        if re1: last_e1[0] = now
        if re2: last_e2[0] = now
        e1 = (now - last_e1[0]) < EMERGENCY_HOLD_SECONDS
        e2 = (now - last_e2[0]) < EMERGENCY_HOLD_SECONDS

        cong1, dur1 = predict_signal(cnt1, hour, "North")
        cong2, dur2 = predict_signal(cnt2, hour, "South")

        (g1, y1, r1, le1,
         g2, y2, r2, le2) = compute_signals(
            cnt1, cnt2, dur1, dur2, e1, e2
        )

        info1 = build_info(
            lane1_name, cnt1, cong1, t1d,
            g1, y1, r1, e1, le1
        )
        info2 = build_info(
            lane2_name, cnt2, cong2, t2d,
            g2, y2, r2, e2, le2
        )

        yield out1, out2, info1, info2

    if cap1: cap1.release()
    if cap2: cap2.release()

# ── CSS ───────────────────────────────────────────────────
css = """
body, .gradio-container {
    background: #0f1117 !important;
    font-family: 'Inter', sans-serif !important;
}
.title-block {
    text-align: center;
    padding: 24px 0 8px 0;
}
.app-title {
    font-size: 26px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: 1px;
    margin: 0;
}
.app-sub {
    color: #475569;
    font-size: 12px;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 4px;
}
.divider {
    height: 1px;
    background: #1e293b;
    margin: 16px 0;
}
label span {
    color: #64748b !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
textarea {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    font-family: 'Courier New', monospace !important;
    font-size: 13px !important;
    line-height: 1.9 !important;
    border-radius: 10px !important;
}
input[type=text], input[type=number] {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
button.primary {
    background: #1d4ed8 !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 15px !important;
    padding: 10px 28px !important;
}
button.primary:hover { background: #2563eb !important; }
.image-container img {
    border-radius: 10px !important;
    border: 1px solid #1e293b !important;
}
.accordion {
    background: #111827 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
}
input[type=range] { accent-color: #2563eb !important; }
.panel-label {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
"""

# ── GRADIO UI ─────────────────────────────────────────────
with gr.Blocks(title="TrafficIQ") as app:

    gr.HTML("""
    <div class="title-block">
        <div class="app-title">🚦 Smart Traffic AI</div>
        <div class="app-sub">Adaptive Signal Control System</div>
    </div>
    <div class="divider"></div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            lane1_name = gr.Textbox(label="Lane 1 Name", value="North Road")
        with gr.Column(scale=1):
            lane2_name = gr.Textbox(label="Lane 2 Name", value="East Road")
        with gr.Column(scale=1):
            hour = gr.Slider(label="Hour of Day", minimum=0, maximum=23,
                             value=8, step=1)
        with gr.Column(scale=1):
            frame_skip = gr.Slider(label="Speed (1=smooth  5=fast)",
                                   minimum=1, maximum=5, value=2, step=1)

    with gr.Row():
        with gr.Column():
            gr.Markdown('<div class="panel-label">📁 Lane 1 Video</div>')
            video1 = gr.Video(label="Lane 1", sources=["upload"])
        with gr.Column():
            gr.Markdown('<div class="panel-label">📁 Lane 2 Video</div>')
            video2 = gr.Video(label="Lane 2", sources=["upload"])

    with gr.Row():
        start_btn = gr.Button("▶  Start System", variant="primary", size="lg")

    gr.HTML("<div class='divider'></div>")

    with gr.Row():
        with gr.Column():
            gr.Markdown('<div class="panel-label">📹 Lane 1 Live Feed</div>')
            out_frame1 = gr.Image(label="Lane 1", show_label=False, height=360)
            info1_box  = gr.Textbox(label="Lane 1 Status", lines=8,
                                    interactive=False)
        with gr.Column():
            gr.Markdown('<div class="panel-label">📹 Lane 2 Live Feed</div>')
            out_frame2 = gr.Image(label="Lane 2", show_label=False, height=360)
            info2_box  = gr.Textbox(label="Lane 2 Status", lines=8,
                                    interactive=False)

    with gr.Accordion("ℹ️ How does TrafficIQ work?", open=False):
        gr.Markdown("""
        **TrafficIQ** uses AI to automatically control traffic signals in real time.

        1. 📹 Two lane videos processed simultaneously
        2. 🤖 YOLOv8 detects and counts all vehicles per frame
        3. 🧠 Random Forest ML predicts congestion level
        4. ⏱️ Signal timing model calculates green light duration
        5. 🚨 Emergency vehicle → immediate green signal for that lane

        **Signal Logic:**
        - Busy lane → 🟢 Green with countdown
        - Other lane → 🔴 Red wait time only
        - Emergency → 🚨 Instant green 20s, other lane red 25s
        """)

    start_btn.click(
        fn      = detect,
        inputs  = [video1, video2, lane1_name, lane2_name, hour, frame_skip],
        outputs = [out_frame1, out_frame2, info1_box, info2_box],
        show_progress = False
    )

if __name__ == "__main__":
    app.launch(
        server_name = "0.0.0.0",
        server_port = 7860,
        inbrowser   = True,
        share       = False,
        css         = css,
        theme       = gr.themes.Base(
            primary_hue = "blue",
            neutral_hue = "slate"
        )
    )