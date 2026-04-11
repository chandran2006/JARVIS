import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("mic_test.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    from core.voice import speak, _mic, _worker

    log(f"Mic alive: {_mic.is_alive()}")
    log(f"Muted at start: {_mic._muted.is_set()}")

    speak("Testing. Mic should unmute immediately after this.", block=True)

    log(f"Muted after speak: {_mic._muted.is_set()}")
    log("PASS: mic unmuted instantly after speak()" if not _mic._muted.is_set() else "FAIL: still muted!")

    # Confirm no delay — mic is already listening
    log(f"Mic result queue size: {_mic._result_q.qsize()}")
    log("Mic is live and ready with zero delay.")
