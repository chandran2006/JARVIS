import cv2
import torch
from ultralytics import YOLO
import time
import sys
import pyttsx3
import threading

def speak(text):
    """Speaks text in a separate thread to avoid blocking video."""
    def _speak():
        try:
            engine = pyttsx3.init()
            # engine.setProperty('rate', 150) 
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")
    
    t = threading.Thread(target=_speak)
    t.start()

def run_vision_system():
    print("--- JARVIS VISION SYSTEM ONLINE ---")
    print("Press 'q' to exit vision mode.")
    
    # 1. Load Model
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Loading YOLOv8 on {device}...")
    try:
        model = YOLO("yolov8n.pt")
        model.to(device)
        print("Model loaded.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # 2. Open Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Tracking for speech
    last_spoken_time = {}
    COOLDOWN = 5.0 # Seconds before speaking same object again
    
    # 3. Live Loop
    prev_time = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Read frame failed.")
            break

        # Run Inference
        results = model(frame, verbose=False) # verbose=False to reduce terminal spam
        
        # Process Detections for Voice
        current_detections = set()
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                current_detections.add(label)
        
        # Voice Logic (DISABLED by user request)
        # current_time = time.time()
        # for obj in current_detections:
        #     # Skip "person" to avoid constant spam since user is always there
        #     if obj == "person": 
        #         continue
        #         
        #     last_time = last_spoken_time.get(obj, 0)
        #     if current_time - last_time > COOLDOWN:
        #         print(f"Speaking: {obj}")
        #         speak(f"I see a {obj}")
        #         last_spoken_time[obj] = current_time
        
        # Annotate
        annotated_frame = results[0].plot()
        
        # Calculate FPS
        curr_time = time.time()
        if curr_time - prev_time > 0:
            fps = 1 / (curr_time - prev_time)
        else:
            fps = 0
        prev_time = curr_time
        
        # Draw FPS
        cv2.putText(annotated_frame, f"FPS: {int(fps)}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show Window
        cv2.imshow("JARVIS Vision System (Press 'q' to Quit)", annotated_frame)

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("--- VISION SYSTEM OFFLINE ---")

if __name__ == "__main__":
    run_vision_system()
