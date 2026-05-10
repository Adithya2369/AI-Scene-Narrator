import cv2
import google.generativeai as genai
from PIL import Image
import numpy as np
import pyttsx3
import threading
import queue
import time

# ==============================
# CONFIG
# ==============================
GEMINI_API_KEY = "YOUR_API_KEY"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ==============================
# THREADED TTS (FAST & RELIABLE)
# ==============================
def speak(text):
    print("[VOICE OUTPUT]:", text)

    try:
        engine = pyttsx3.init('sapi5')  # fresh engine every time
        engine.setProperty('rate', 170)

        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id)

        engine.say(text)
        engine.runAndWait()

        engine.stop()
        del engine  # 🔥 VERY IMPORTANT

        time.sleep(0.2)  # prevents overlap crash

    except Exception as e:
        print("[TTS ERROR]:", str(e))

# ==============================
# CAMERA CAPTURE
# ==============================
def capture_image(camera_index, name):
    print(f"[INFO] Accessing {name} camera...")

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"[ERROR] {name} camera not accessible")
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"[ERROR] Failed to capture from {name} camera")
        return None

    if not is_valid_frame(frame, name):
        print(f"[ERROR] {name} camera returned invalid frame")
        return None

    print(f"[SUCCESS] {name} image captured and validated")
    return frame

# ==============================
# VALIDATION
# ==============================
def is_valid_frame(frame, name):
    if frame is None:
        print(f"[DEBUG] {name} frame is None")
        return False

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    variance = np.var(gray)

    print(f"[DEBUG] {name} variance: {variance}")

    if variance < 10:
        print(f"[WARNING] {name} frame seems invalid")
        return False

    return True

# ==============================
# CONVERT IMAGE
# ==============================
def convert_to_pil(frame):
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

# ==============================
# GEMINI PROCESSING
# ==============================
def describe_image(image, label):
    prompt = f"""
    Describe this image briefly (under 30 words).
    Start with "{label} scene:".
    Focus only on important objects or obstacles.
    """

    print(f"[INFO] Sending {label} image to Gemini...")

    response = model.generate_content([prompt, image])

    result = response.text.strip()
    print(f"[RESULT - {label}]: {result}")

    return result

# ==============================
# MAIN LOGIC
# ==============================
def main():
    print("=== SMART SCENE VOICE SYSTEM STARTED ===")

    front_frame = capture_image(0, "Front")
    back_frame = capture_image(1, "Back")

    # BOTH WORKING
    if front_frame is not None and back_frame is not None:
        speak("Scanning surroundings")

        front_desc = describe_image(convert_to_pil(front_frame), "Front")
        speak(front_desc)

        time.sleep(1)

        back_desc = describe_image(convert_to_pil(back_frame), "Back")
        speak(back_desc)

    # FRONT FAILED
    elif front_frame is None and back_frame is not None:
        speak("Front camera is not responding")

        back_desc = describe_image(convert_to_pil(back_frame), "Back")
        speak(back_desc)

    # BACK FAILED
    elif back_frame is None and front_frame is not None:
        speak("Back camera is not responding")

        front_desc = describe_image(convert_to_pil(front_frame), "Front")
        speak(front_desc)

    # BOTH FAILED
    else:
        speak("Both cameras are not responding")
        print("[CRITICAL] No cameras available")

    print("=== PROCESS COMPLETE ===")

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    main()