import streamlit as st
import cv2
import joblib
import pandas as pd
import tempfile
import time
from ultralytics import YOLO

# ── CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Traffic AI",
    page_icon="🚦",
    layout="wide" 
)

# Fix 2: Applied cleaner info panel font and layout
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }

.main-title {
    font-size: 22px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}

/* ── Lane heading ── */
.lane-heading {
    font-size: 16px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: 0.5px;
    margin: 8px 0 10px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e293b;
}

/* ── Info card ── */
.info-list {
    background: #111827;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 0;
    margin: 4px 0;
    overflow: hidden;
}
.info-list li {
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 400;
    padding: 10px 14px;
    list-style: none;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #1a2333;
    gap: 8px;
}
.info-list li:last-child { border-bottom: none; }
.info-list li b { color: #94a3b8; font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Signal badges ── */
.sig-green {
    background: #052e16;
    border: 1px solid #16a34a;
    border-radius: 20px;
    padding: 3px 10px;
    color: #4ade80;
    font-weight: 600;
    font-size: 12px;
    white-space: nowrap;
}
.sig-yellow {
    background: #1c1400;
    border: 1px solid #ca8a04;
    border-radius: 20px;
    padding: 3px 10px;
    color: #facc15;
    font-weight: 600;
    font-size: 12px;
    white-space: nowrap;
}
.sig-red {
    background: #1c0505;
    border: 1px solid #dc2626;
    border-radius: 20px;
    padding: 3px 10px;
    color: #f87171;
    font-weight: 600;
    font-size: 12px;
    white-space: nowrap;
}
.sig-emergency {
    background: #1c0800;
    border: 1px solid #ea580c;
    border-radius: 20px;
    padding: 3px 10px;
    color: #fb923c;
    font-weight: 700;
    font-size: 12px;
    white-space: nowrap;
}
.sig-inactive {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 20px;
    padding: 3px 10px;
    color: #1e293b;
    font-size: 12px;
    white-space: nowrap;
}
.video-caption {
    text-align: center;
    color: #334155;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 6px;
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── LOAD MODELS ──────────────────────────────────────────
@st.cache_resource
def load_models():
    yolo    = YOLO("models/best.pt")
    clf     = joblib.load("models/classifier.pkl")
    reg     = joblib.load("models/regressor.pkl")
    le_lane = joblib.load("models/le_lane.pkl")
    le_cong = joblib.load("models/le_congestion.pkl")
    return yolo, clf, reg, le_lane, le_cong

yolo, clf, reg, le_lane, le_cong = load_models()

# ── SETTINGS ─────────────────────────────────────────────
EMERGENCY_CLASSES = ["ambulance", "fire truck", "police", "paramedic","Ambulance"]
EMERGENCY_GREEN_TIME   = 20
EMERGENCY_RED_TIME     = 25
EMERGENCY_HOLD_SECONDS = 5
YELLOW_DURATION        = 3

# ── SIGNAL PREDICTION ─────────────────────────────────────
def predict_signal(count, hour, lane):
    try:
        lane_enc = le_lane.transform([lane])[0]
    except:
        lane_enc = 0
    X = pd.DataFrame([[count, hour, lane_enc]], columns=["vehicle_count", "hour", "lane_encoded"])
    congestion = le_cong.inverse_transform(clf.predict(X))[0]
    duration   = int(reg.predict(X)[0])
    return congestion, min(duration, 120)

# ── PROCESS FRAME ─────────────────────────────────────────
def process_frame(frame, lane_name, lane_number):
    frame = cv2.resize(frame, (640, 360))
    results = yolo.track(frame, conf=0.25, iou=0.45, imgsz=640, persist=True, tracker="bytetrack.yaml", verbose=False)[0]

    tracked_ids = set()
    fallback_count = 0
    has_emergency = False
    type_counts = {}

    if results.boxes is not None:
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_name = yolo.model.names[int(box.cls[0])]
            type_counts[cls_name] = type_counts.get(cls_name, 0) + 1
            if box.id is not None:
                try: tracked_ids.add(int(box.id[0]))
                except: pass
            fallback_count += 1

            is_emergency = any(e in cls_name.lower() for e in EMERGENCY_CLASSES)
            box_color = (0, 0, 255) if is_emergency else (0, 255, 80)
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            
            label = "EMERGENCY" if is_emergency else cls_name.upper()
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (x1, y1-lh-10), (x1+lw+5, y1), box_color, -1)
            cv2.putText(frame, label, (x1+2, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,0), 1)
            if is_emergency: has_emergency = True

    vehicle_count = len(tracked_ids) if tracked_ids else fallback_count

    # Fix 1: Smaller cleaner overlay on video
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (200, 52), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    cv2.putText(frame, f"LANE {lane_number}  |  {lane_name.upper()}", (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 200, 255), 1)
    cv2.putText(frame, f"VEHICLES: {vehicle_count}", (8, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    if has_emergency:
        h_frame = frame.shape[0]
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, h_frame-28), (frame.shape[1], h_frame), (150, 0, 0), -1)
        cv2.addWeighted(overlay2, 0.8, frame, 0.2, 0, frame)
        cv2.putText(frame, "EMERGENCY DETECTED", (8, h_frame-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 80, 80), 1)

    return frame, vehicle_count, has_emergency, type_counts

# ── SIGNAL DISPLAY ────────────────────────────────────────
def render_signals(green_sec, yellow_sec, red_sec, is_emergency=False):
    if is_emergency:
        return f'<span class="sig-emergency">🚨 EMERGENCY GREEN: {green_sec}s</span>'
    parts = []
    if green_sec > 0: parts.append(f'<span class="sig-green">🟢 Green: {green_sec}s</span>')
    elif yellow_sec > 0: parts.append(f'<span class="sig-yellow">🟡 Yellow: {yellow_sec}s</span>')
    elif red_sec > 0: parts.append(f'<span class="sig-red">🔴 Red: {red_sec}s</span>')
    else: parts.append(f'<span class="sig-inactive">🚦 Inactive</span>')
    return " ".join(parts)

# ── MAIN UI ──────────────────────────────────────────────
st.markdown('<div class="main-title">🚦 Smart Traffic AI – Adaptive Signal Control</div>', unsafe_allow_html=True)
st.markdown("---")

st.sidebar.title("⚙️ Settings")
hour = st.sidebar.slider("🕐 Hour of Day", 0, 23, 8)
lane1_name = st.sidebar.text_input("Lane 1 Name", value="North Road")
lane2_name = st.sidebar.text_input("Lane 2 Name", value="East Road")
frame_skip = st.sidebar.slider("Process every N frames", 1, 5, 2)

up1, up2 = st.columns(2)
with up1: video1 = st.file_uploader(f"📁 {lane1_name} Video", type=["mp4","avi","mov","mkv"])
with up2: video2 = st.file_uploader(f"📁 {lane2_name} Video", type=["mp4","avi","mov","mkv"])

b1, b2, _ = st.columns([1, 1, 5])
start_btn, stop_btn = b1.button("▶ Start System", type="primary"), b2.button("⏹ Stop")

if stop_btn:
    st.session_state["stop"] = True
    st.rerun()

if start_btn and (video1 or video2):
    st.session_state["stop"] = False
    vcol1, vcol2 = st.columns(2)
    frame_ph1, frame_ph2 = vcol1.empty(), vcol2.empty()
    vcol1.markdown(f'<div class="video-caption">{lane1_name}</div>', unsafe_allow_html=True)
    vcol2.markdown(f'<div class="video-caption">{lane2_name}</div>', unsafe_allow_html=True)
    st.markdown("---")
    info_col1, info_col2 = st.columns(2)
    with info_col1: ph_head1, ph_info1 = st.empty(), st.empty()
    with info_col2: ph_head2, ph_info2 = st.empty(), st.empty()

    cap1 = cap2 = None
    if video1:
        t1 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        t1.write(video1.read())
        cap1 = cv2.VideoCapture(t1.name)
    if video2:
        t2 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        t2.write(video2.read())
        cap2 = cv2.VideoCapture(t2.name)

    last_emerg1 = last_emerg2 = 0.0
    frame_count = 0

    while not st.session_state.get("stop", False):
        frame_count += 1
        f1 = f2 = None
        if cap1 and cap1.isOpened():
            ret1, f1 = cap1.read()
            if not ret1: cap1.set(cv2.CAP_PROP_POS_FRAMES, 0); _, f1 = cap1.read()
        if cap2 and cap2.isOpened():
            ret2, f2 = cap2.read()
            if not ret2: cap2.set(cv2.CAP_PROP_POS_FRAMES, 0); _, f2 = cap2.read()

        if frame_count % frame_skip != 0: continue

        if f1 is not None:
            f1, cnt1, raw_e1, types1 = process_frame(f1, lane1_name, 1)
            frame_ph1.image(cv2.cvtColor(f1, cv2.COLOR_BGR2RGB), use_container_width=True)
        if f2 is not None:
            f2, cnt2, raw_e2, types2 = process_frame(f2, lane2_name, 2)
            frame_ph2.image(cv2.cvtColor(f2, cv2.COLOR_BGR2RGB), use_container_width=True)

        now = time.time()
        if raw_e1: last_emerg1 = now
        if raw_e2: last_emerg2 = now
        e1, e2 = (now - last_emerg1) < EMERGENCY_HOLD_SECONDS, (now - last_emerg2) < EMERGENCY_HOLD_SECONDS

        cong1, dur1 = predict_signal(cnt1, hour, "North")
        cong2, dur2 = predict_signal(cnt2, hour, "South")

        if e1 and not e2:
            g1_green, g1_red, g2_green, g2_red = EMERGENCY_GREEN_TIME, 0, 0, EMERGENCY_RED_TIME
            l1_e, l2_e = True, False
        elif e2 and not e1:
            g1_green, g1_red, g2_green, g2_red = 0, EMERGENCY_RED_TIME, EMERGENCY_GREEN_TIME, 0
            l1_e, l2_e = False, True
        elif cnt1 >= cnt2:
            g1_green, g1_red, g2_green, g2_red = dur1, 0, 0, dur1 + YELLOW_DURATION
            l1_e, l2_e = False, False
        else:
            g1_green, g1_red, g2_green, g2_red = 0, dur2 + YELLOW_DURATION, dur2, 0
            l1_e, l2_e = False, False

        signals1_html = render_signals(g1_green, 0, g1_red, l1_e)
        signals2_html = render_signals(g2_green, 0, g2_red, l2_e)
        types1_str = " | ".join([f"{k}: {v}" for k, v in sorted(types1.items())]) if types1 else "..."
        types2_str = " | ".join([f"{k}: {v}" for k, v in sorted(types2.items())]) if types2 else "..."

        ph_head1.markdown(f'<div class="lane-heading">📍 {lane1_name}</div>', unsafe_allow_html=True)
        # Fix 3: Cleaner info panel content
        ph_info1.markdown(f"""
        <div class="info-list">
            <li><b>Vehicles</b> <span style="color:#fff;font-size:20px;font-weight:700">{cnt1}</span></li>
            <li><b>Signal</b> <span>{signals1_html}</span></li>
            <li><b>Congestion</b> <span style="color:#94a3b8">{cong1}</span></li>
            <li><b>Emergency</b> <span style="color:{'#fb923c' if e1 else '#334155'}">{'YES 🚨' if e1 else 'NO'}</span></li>
            <li><b>Types</b> <span style="color:#64748b;font-size:12px">{types1_str}</span></li>
        </div>
        """, unsafe_allow_html=True)

        ph_head2.markdown(f'<div class="lane-heading">📍 {lane2_name}</div>', unsafe_allow_html=True)
        ph_info2.markdown(f"""
        <div class="info-list">
            <li><b>Vehicles</b> <span style="color:#fff;font-size:20px;font-weight:700">{cnt2}</span></li>
            <li><b>Signal</b> <span>{signals2_html}</span></li>
            <li><b>Congestion</b> <span style="color:#94a3b8">{cong2}</span></li>
            <li><b>Emergency</b> <span style="color:{'#fb923c' if e2 else '#334155'}">{'YES 🚨' if e2 else 'NO'}</span></li>
            <li><b>Types</b> <span style="color:#64748b;font-size:12px">{types2_str}</span></li>
        </div>
        """, unsafe_allow_html=True)

        time.sleep(0.01)

    if cap1: cap1.release()
    if cap2: cap2.release()
    st.success("✅ System stopped.")