import gradio as gr
import random
from PIL import Image, ImageDraw

def process_video(video, lane_name):
    # This is a mock function that simulates processing a video frame
    # and detecting vehicles with YOLOv8.
    
    # Create a mock image frame
    img = Image.new('RGB', (640, 480), color=(15, 20, 35))
    draw = ImageDraw.Draw(img)
    
    # Draw some "detected" bounding boxes
    num_vehicles = random.randint(2, 15)
    for _ in range(num_vehicles):
        x1 = random.randint(50, 500)
        y1 = random.randint(50, 350)
        x2 = x1 + random.randint(40, 100)
        y2 = y1 + random.randint(40, 100)
        
        draw.rectangle([x1, y1, x2, y2], outline="#00ff88", width=3)
        draw.text((x1, y1 - 15), "car 0.95", fill="#00ff88")
        
    draw.text((20, 20), f"Lane: {lane_name}", fill="#00e5ff")
    draw.text((20, 40), f"Vehicles: {num_vehicles}", fill="#00e5ff")
    draw.text((20, 60), "LIVE AI DETECTION", fill="#ff4757")
    
    return img, num_vehicles

def detect_traffic(video1, video2, lane1_name, lane2_name, hour, frame_skip):
    try:
        # Generate mock frames and stats
        img1, l1_count = process_video(video1, lane1_name)
        img2, l2_count = process_video(video2, lane2_name)
        
        # Calculate congestion levels based on mock counts
        def get_congestion(count):
            if count < 5: return "Low"
            if count < 10: return "Medium"
            return "High"
            
        l1_cong = get_congestion(l1_count)
        l2_cong = get_congestion(l2_count)
        
        # Basic traffic light logic: Green for the lane with more traffic
        if l1_count >= l2_count:
            l1_signal, l2_signal = "Green", "Red"
        else:
            l1_signal, l2_signal = "Red", "Green"
            
        emergency_alert = random.random() > 0.95 # 5% chance of emergency
        
        return img1, img2, l1_count, l2_count, l1_cong, l2_cong, l1_signal, l2_signal, emergency_alert
    except Exception as e:
        print(f"Error: {e}")
        # Return empty/default if failure
        img = Image.new('RGB', (640, 480), color=(0, 0, 0))
        return img, img, 0, 0, "Low", "Low", "Red", "Red", False

with gr.Blocks() as app:
    with gr.Row():
        v1 = gr.File(label="Video 1")
        v2 = gr.File(label="Video 2")
        l1 = gr.Textbox(label="Lane 1")
        l2 = gr.Textbox(label="Lane 2")
        h = gr.Number(label="Hour")
        fs = gr.Number(label="Frame Skip")
    
    with gr.Row():
        out_img1 = gr.Image(type="filepath")
        out_img2 = gr.Image(type="filepath")
        out_c1 = gr.Number()
        out_c2 = gr.Number()
        out_cg1 = gr.Textbox()
        out_cg2 = gr.Textbox()
        out_s1 = gr.Textbox()
        out_s2 = gr.Textbox()
        out_alert = gr.Checkbox()
        
    btn = gr.Button("Detect")
    btn.click(
        fn=detect_traffic,
        inputs=[v1, v2, l1, l2, h, fs],
        outputs=[out_img1, out_img2, out_c1, out_c2, out_cg1, out_cg2, out_s1, out_s2, out_alert],
        api_name="detect"
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
