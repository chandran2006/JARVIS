import os
import sys
import asyncio
import cv2
import pyaudio
import io
from dotenv import load_dotenv

# Try importing the new SDK
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("Error: google-genai not installed.")

# Audio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE_IN = 16000
RATE_OUT = 24000
CHUNK = 1024

async def run_live_session():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return

    model_id = "gemini-2.5-flash-native-audio-latest"
    print(f"[Gemini Live] Connecting to model: {model_id}")
    
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
    
    # Helper to grab video frames
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Audio Setup
    p = pyaudio.PyAudio()
    
    try:
        mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE_IN, input=True, frames_per_buffer=CHUNK)
        spk_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE_OUT, output=True)
    except Exception as e:
        print(f"Audio Error: {e}")
        return

    print("[Gemini Live] Connected to peripherals.")
    print("[Gemini Live] Press 'q' in the video window to exit.")

    # Shared Reference for breaking loops
    state = {"running": True}

    try:
        # Connect to Live API
        config = {"response_modalities": ["AUDIO"]}
        async with client.aio.live.connect(model=model_id, config=config) as session:
            print("[Gemini Live] Connected to Gemini. Say hello!")

            # 1. Send Audio Task
            async def send_audio():
                while state["running"]:
                    try:
                        data = mic_stream.read(CHUNK, exception_on_overflow=False)
                        await session.send(input={"mime_type": "audio/pcm;rate=16000", "data": data}, end_of_turn=False)
                        await asyncio.sleep(0.001)
                    except Exception as e:
                        print(f"Audio Send Error: {e}")
                        break

            # Shared frame storage
            latest_frame_data = {"frame": None}

            # 2. Capture and Display Task (Runs at ~24 FPS)
            async def capture_and_display():
                while state["running"]:
                    ret, frame = cap.read()
                    if not ret:
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Resize for bandwidth/display
                    frame_small = cv2.resize(frame, (640, 480))
                    
                    # Show Local Window
                    cv2.imshow("Gemini Live Vision", frame_small)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        state["running"] = False
                        break
                    
                    # Update shared frame
                    latest_frame_data["frame"] = frame_small
                    
                    # Target ~24 FPS
                    await asyncio.sleep(0.04)

            # 3. Transmit Task (Sends 1 frame per second to save tokens)
            async def transmit_video():
                while state["running"]:
                    if latest_frame_data["frame"] is not None:
                        frame = latest_frame_data["frame"]
                        # Encode for sending
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 40])
                        
                        try:
                            await session.send(input={"mime_type": "image/jpeg", "data": buffer.tobytes()}, end_of_turn=False)
                        except Exception as e:
                            print(f"Video Send Error: {e}")
                    
                    # Send every 1.0 second
                    await asyncio.sleep(1.0)

            # 3. Receive Task
            async def receive_audio():
                while state["running"]:
                    try:
                        async for response in session.receive():
                            if not state["running"]: break
                            
                            server_content = response.server_content
                            if server_content and server_content.model_turn:
                                for part in server_content.model_turn.parts:
                                    if part.inline_data:
                                        spk_stream.write(part.inline_data.data)
                                    if part.text:
                                         print(f"Gemini: {part.text}")
                    except Exception as e:
                        print(f"Receive Error: {e}")
                        state["running"] = False

            # Run Concurrent Tasks
            await asyncio.gather(send_audio(), capture_and_display(), transmit_video(), receive_audio())

    except Exception as e:
        print(f"Session Error: {e}")
    finally:
        state["running"] = False
        if 'mic_stream' in locals(): 
            mic_stream.stop_stream()
            mic_stream.close()
        if 'spk_stream' in locals():
            spk_stream.stop_stream()
            spk_stream.close()
        p.terminate()
        cap.release()
        cv2.destroyAllWindows()
        print("[Gemini Live] Session Ended.")

if __name__ == "__main__":
    if not HAS_GENAI:
        print("Please install google-genai first.")
    else:
        asyncio.run(run_live_session())
