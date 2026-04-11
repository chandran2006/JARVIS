import sys, time, threading
sys.path.insert(0, r"c:\Users\ganes\OneDrive\Desktop\Project_JARVIS-main")

# Patch to trace the worker internals
import core.voice as v

original_run = v._TTSWorker.run

def patched_run(self):
    import pyttsx3
    self._engine = pyttsx3.init()
    self._engine.setProperty("rate", 150)
    self._engine.setProperty("volume", 1.0)
    self._pick_voice()
    print("[Worker] Engine ready, entering loop", flush=True)

    while True:
        self._trigger.wait()
        self._trigger.clear()
        print("[Worker] Trigger received", flush=True)
        while True:
            with self._lock:
                if not self._queue:
                    break
                text = self._queue.pop(0)
            print(f"[Worker] Speaking: {text[:40]}", flush=True)
            self._speaking = True
            self._done.clear()
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                print("[Worker] runAndWait complete", flush=True)
            except Exception as e:
                print(f"[Worker] ERROR: {e}", flush=True)
            finally:
                self._speaking = False
        self._done.set()
        print("[Worker] Done set", flush=True)

v._TTSWorker.run = patched_run

# Re-create worker with patched run
worker = v._TTSWorker()
time.sleep(0.5)  # let engine init

print("Calling speak...", flush=True)
v._worker = worker
v.speak("Good morning sir. JARVIS online.", block=True)
print("speak() returned", flush=True)
