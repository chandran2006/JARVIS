import os
import sys
import json
import threading
import queue
import subprocess
import speech_recognition as sr

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── JSON → plain text ─────────────────────────────────────────────────────────
def _to_speech(text: str) -> str:
    text = str(text).strip()
    if not text or "{" not in text:
        return text
    try:
        d = json.loads(text)
        if "message" in d:
            return str(d["message"]).strip()
        if d.get("status") == "error":
            return d.get("message", "Something went wrong.")
        for k in ("datetime", "time", "date", "day", "value", "content"):
            if k in d:
                return str(d[k])
        if d.get("status") == "success":
            return "Done, sir."
        pairs = [f"{k} is {v}" for k, v in d.items() if k != "status" and v]
        return ". ".join(pairs) if pairs else "Done, sir."
    except Exception:
        return text

# ── Persistent PowerShell SAPI speaker ───────────────────────────────────────
_PS_INIT = """
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 1
$synth.Volume = 100
$voices = $synth.GetInstalledVoices()
foreach ($v in $voices) {
    $name = $v.VoiceInfo.Name.ToLower()
    if ($name -like '*david*' -or $name -like '*mark*' -or $name -like '*george*') {
        $synth.SelectVoice($v.VoiceInfo.Name)
        break
    }
}
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
while ($true) {
    $line = [Console]::ReadLine()
    if ($line -eq $null -or $line -eq 'EXIT') { break }
    if ($line.Trim() -ne '') { $synth.Speak($line) }
    Write-Host 'DONE'
    [Console]::Out.Flush()
}
"""

class _PersistentSpeaker:
    def __init__(self):
        self._proc = None
        self._lock = threading.Lock()
        self._start()

    def _start(self):
        try:
            self._proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_INIT],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except Exception as ex:
            print(f"[Speaker] {ex}", flush=True)
            self._proc = None

    def speak(self, text: str) -> bool:
        with self._lock:
            if self._proc is None or self._proc.poll() is not None:
                self._start()
            if self._proc is None:
                return False
            try:
                line = text.replace("\n", " ").replace("\r", " ") + "\n"
                self._proc.stdin.write(line.encode("utf-8", errors="replace"))
                self._proc.stdin.flush()
                while True:
                    out = self._proc.stdout.readline().decode("utf-8", errors="replace").strip()
                    if out == "DONE":
                        return True
                    if not out and self._proc.poll() is not None:
                        return False
            except Exception as ex:
                print(f"[Speaker] {ex}", flush=True)
                self._proc = None
                return False

_speaker = _PersistentSpeaker()

# ── TTS Worker ────────────────────────────────────────────────────────────────
class _TTSWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="TTS-Worker")
        self._q    = queue.Queue()
        self._busy = False
        self._done = threading.Event()
        self._done.set()
        self.start()

    def run(self):
        while True:
            text = self._q.get()
            if text is None:
                break
            self._busy = True
            self._done.clear()
            try:
                ok = _speaker.speak(text)
                if not ok:
                    self._fallback(text)
            except Exception as ex:
                print(f"[TTS] {ex}", flush=True)
            finally:
                self._busy = False
                self._done.set()

    def _fallback(self, text: str):
        try:
            script = (
                "import pyttsx3; e=pyttsx3.init(); "
                "e.setProperty('rate',160); "
                f"e.say({repr(text)}); e.runAndWait()"
            )
            subprocess.run(
                [sys.executable, "-c", script], timeout=30, capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except Exception:
            pass

    def say(self, text: str):
        while not self._q.empty():
            try: self._q.get_nowait()
            except Exception: break
        self._done.clear()
        self._q.put(text)

    def is_busy(self) -> bool:
        return self._busy or not self._q.empty()

    def wait(self, timeout: float = 60):
        self._done.wait(timeout=timeout)

_worker = _TTSWorker()

# ── Persistent Microphone Listener ────────────────────────────────────────────
# Mic stays open always — no open/close overhead, no ambient noise re-calibration
class _MicListener(threading.Thread):
    """
    Runs in background, continuously captures audio.
    When JARVIS is speaking, captured audio is discarded (echo prevention).
    Results go into _audio_queue for listen() to pick up instantly.
    """
    def __init__(self):
        super().__init__(daemon=True, name="Mic-Listener")
        self._result_q  = queue.Queue(maxsize=1)
        self._muted     = threading.Event()   # set = discard audio (JARVIS speaking)
        self._recognizer = sr.Recognizer()
        self._recognizer.pause_threshold       = 0.6
        self._recognizer.non_speaking_duration = 0.3
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.energy_threshold      = 300
        self.start()

    def mute(self):
        """Call when JARVIS starts speaking — discard mic input."""
        self._muted.set()

    def unmute(self):
        """Call when JARVIS finishes speaking — start accepting input."""
        # Drain any stale results captured while speaking
        while not self._result_q.empty():
            try: self._result_q.get_nowait()
            except Exception: break
        self._muted.clear()

    def run(self):
        try:
            mic = sr.Microphone()
        except Exception as ex:
            print(f"[Mic] Cannot open microphone: {ex}", flush=True)
            return

        # One-time calibration at startup
        with mic as src:
            try:
                self._recognizer.adjust_for_ambient_noise(src, duration=0.5)
                print("[Mic] Calibrated and ready.", flush=True)
            except Exception:
                pass

        while True:
            try:
                with mic as src:
                    # Short timeout so we loop quickly and check mute state
                    audio = self._recognizer.listen(
                        src, timeout=3, phrase_time_limit=10
                    )

                # If JARVIS is speaking, throw away what we heard
                if self._muted.is_set():
                    continue

                # Recognise in background thread — non-blocking for the listener
                threading.Thread(
                    target=self._recognise, args=(audio,), daemon=True
                ).start()

            except sr.WaitTimeoutError:
                continue
            except Exception as ex:
                print(f"[Mic] {ex}", flush=True)
                import time; time.sleep(0.5)

    def _recognise(self, audio):
        if self._muted.is_set():
            return
        try:
            text = self._recognizer.recognize_google(audio, language="en-IN")
            text = text.lower().strip()
            if text:
                print(f"YOU: {text}", flush=True)
                # Only keep the latest — drop old if queue full
                if self._result_q.full():
                    try: self._result_q.get_nowait()
                    except Exception: pass
                self._result_q.put(text)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"[Speech API] {e}", flush=True)
        except Exception as e:
            print(f"[Recognise] {e}", flush=True)

    def get(self, timeout: float = 7) -> str:
        """Block until a result is available, return 'none' on timeout."""
        try:
            return self._result_q.get(timeout=timeout)
        except queue.Empty:
            return "none"

_mic = _MicListener()

# ── Public API ────────────────────────────────────────────────────────────────
def speak(text: str, block: bool = True):
    text = _to_speech(text).strip()
    if not text:
        return
    try:
        print(f"\nJARVIS: {text}\n", flush=True)
    except Exception:
        pass
    _mic.mute()          # stop accepting mic input while speaking
    _worker.say(text)
    if block:
        _worker.wait()
        _mic.unmute()    # immediately ready to listen again


def is_speaking() -> bool:
    return _worker.is_busy()


def listen(timeout: int = 7, phrase_limit: int = 12) -> str:
    """Returns the next recognised phrase instantly — mic is always on."""
    print("[Listening...]", flush=True)
    return _mic.get(timeout=timeout)
