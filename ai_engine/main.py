import cv2
import asyncio
import random
import time
import numpy as np
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
traffic_state = {
    "running": False,
    "lane1": {"count": 0, "congestion": "Low", "emergency": False, "breakdown": {"Car": 0, "Truck": 0, "Bus": 0, "Emergency": 0}, "signal": "Red"},
    "lane2": {"count": 0, "congestion": "Low", "emergency": False, "breakdown": {"Car": 0, "Truck": 0, "Bus": 0, "Emergency": 0}, "signal": "Green"},
}

class MockLane:
    def __init__(self, lane_id):
        self.lane_id = lane_id
        self.detections = []
    
    def update(self):
        # Move boxes down
        for d in self.detections:
            d['y'] += 10
            d['x'] += random.randint(-2, 2)
        
        # Remove off-screen
        self.detections = [d for d in self.detections if d['y'] < 480]
        
        has_emergency = traffic_state[self.lane_id]["emergency"]
        
        # Add new boxes to maintain a random count between 1 and 6
        target_count = random.randint(1, 6)
        while len(self.detections) < target_count:
            types = ['Car', 'Truck', 'Bus']
            is_emergency = has_emergency and not any(d['isEmergency'] for d in self.detections)
            type_str = 'Emergency' if is_emergency else random.choice(types)
            
            self.detections.append({
                'id': random.randint(1000, 9999),
                'type': type_str.upper(),
                'isEmergency': is_emergency,
                'x': random.randint(200, 400), # Middle spawn
                'y': random.randint(100, 200),
                'width': random.randint(40, 80),
                'height': random.randint(60, 100)
            })
            
        # Limit
        if len(self.detections) > target_count:
            self.detections = self.detections[:target_count]
            
        # Update breakdown
        breakdown = {"Car": 0, "Truck": 0, "Bus": 0, "Emergency": 0}
        for d in self.detections:
            t = "Emergency" if d["isEmergency"] else d["type"].capitalize()
            breakdown[t] += 1
            
        traffic_state[self.lane_id]["count"] = len(self.detections)
        traffic_state[self.lane_id]["breakdown"] = breakdown
        if len(self.detections) < 3:
            traffic_state[self.lane_id]["congestion"] = "Low"
        elif len(self.detections) < 5:
            traffic_state[self.lane_id]["congestion"] = "Medium"
        else:
            traffic_state[self.lane_id]["congestion"] = "High"

lane1_mock = MockLane("lane1")
lane2_mock = MockLane("lane2")

def draw_corner_brackets(img, x, y, w, h, color, thickness):
    length = 15
    # Top-left
    cv2.line(img, (x, y), (x + length, y), color, thickness)
    cv2.line(img, (x, y), (x, y + length), color, thickness)
    # Top-right
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness)
    # Bottom-left
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness)
    # Bottom-right
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness)

async def generate_frames(lane_mock: MockLane):
    # Colors in OpenCV are BGR
    # Dark blue-gray background: #05070d -> (13, 7, 5)
    while True:
        if not traffic_state["running"]:
            await asyncio.sleep(1)
            continue
            
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (20, 10, 10) 
        
        # Draw road perspective
        cv2.polylines(img, [np.array([[200, 100], [440, 100], [600, 480], [40, 480]])], True, (40, 40, 40), 2)
        
        lane_mock.update()
        
        for det in lane_mock.detections:
            x, y, w, h = det['x'], det['y'], det['width'], det['height']
            is_emergency = det['isEmergency']
            
            # Neon Teal is #00f2ea -> RGB (0, 242, 234) -> BGR (234, 242, 0)
            # Bright Red is #ff0000 -> RGB (255, 0, 0) -> BGR (0, 0, 255)
            color = (0, 0, 255) if is_emergency else (234, 242, 0) 
            thickness = 3 if is_emergency else 1
            
            draw_corner_brackets(img, x, y, w, h, color, thickness)
            
            if is_emergency:
                # Pulsating text
                pulse = int((time.time() * 5) % 2)
                text_color = (0, 0, 255) if pulse == 0 else (0, 0, 150)
                cv2.putText(img, "EMERGENCY", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        await asyncio.sleep(0.1) # 10 FPS

@app.get("/video_feed/lane1")
async def video_feed_lane1():
    return StreamingResponse(generate_frames(lane1_mock), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/video_feed/lane2")
async def video_feed_lane2():
    return StreamingResponse(generate_frames(lane2_mock), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/ai-api/data")
async def get_data():
    return traffic_state

class StartRequest(BaseModel):
    video1: str = ""
    video2: str = ""
    hour: int = 12

@app.post("/ai-api/start")
async def start_system(req: StartRequest):
    traffic_state["running"] = True
    return {"status": "started"}

@app.post("/ai-api/stop")
async def stop_system():
    traffic_state["running"] = False
    return {"status": "stopped"}

@app.get("/ai-api/status")
async def status():
    return {"running": traffic_state["running"]}

# Random emergency trigger
async def emergency_trigger():
    while True:
        await asyncio.sleep(random.randint(5, 15))
        if traffic_state["running"]:
            lane = random.choice(["lane1", "lane2"])
            traffic_state[lane]["emergency"] = True
            await asyncio.sleep(5)
            traffic_state[lane]["emergency"] = False

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(emergency_trigger())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
