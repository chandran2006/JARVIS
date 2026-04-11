import sys, traceback
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("bv_test.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    # ── Volume test ──────────────────────────────────────────────────────────
    log("=== VOLUME ===")

    # Method 1: pycaw
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interface, POINTER(IAudioEndpointVolume))
        vol.SetMasterVolumeLevelScalar(0.5, None)
        log("pycaw volume set to 50%: OK")
    except Exception as e:
        log(f"pycaw FAILED: {e}")

    # Method 2: PowerShell nircmd
    try:
        import subprocess
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"],
            capture_output=True, timeout=5
        )
        log(f"PowerShell SendKeys: returncode={r.returncode} err={r.stderr.decode(errors='replace').strip()}")
    except Exception as e:
        log(f"PowerShell SendKeys FAILED: {e}")

    # Method 3: Windows API SetVolume via ctypes directly
    try:
        import subprocess
        script = """
$obj = New-Object -ComObject WScript.Shell
1..50 | ForEach-Object { $obj.SendKeys([char]174) }
$target = 50
$steps = [int]($target / 2)
1..$steps | ForEach-Object { $obj.SendKeys([char]175) }
Write-Host "DONE"
"""
        r = subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command",script],
                           capture_output=True, timeout=15)
        log(f"Volume via SendKeys loop: {r.stdout.decode(errors='replace').strip()} err={r.stderr.decode(errors='replace').strip()[:100]}")
    except Exception as e:
        log(f"SendKeys loop FAILED: {e}")

    # ── Brightness test ──────────────────────────────────────────────────────
    log("\n=== BRIGHTNESS ===")

    # Method 1: screen_brightness_control
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()
        log(f"sbc current brightness: {current}")
        sbc.set_brightness(70)
        log("sbc set_brightness(70): OK")
    except Exception as e:
        log(f"sbc FAILED: {e}\n{traceback.format_exc()}")

    # Method 2: WMI PowerShell
    try:
        import subprocess
        script = "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,70)"
        r = subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command",script],
                           capture_output=True, timeout=10)
        log(f"WMI brightness: returncode={r.returncode} out={r.stdout.decode(errors='replace').strip()} err={r.stderr.decode(errors='replace').strip()[:200]}")
    except Exception as e:
        log(f"WMI FAILED: {e}")

    # Method 3: PowerShell Get-WmiObject alternative
    try:
        import subprocess
        script = "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods).WmiSetBrightness(1,70)"
        r = subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command",script],
                           capture_output=True, timeout=10)
        log(f"CIM brightness: returncode={r.returncode} out={r.stdout.decode(errors='replace').strip()} err={r.stderr.decode(errors='replace').strip()[:200]}")
    except Exception as e:
        log(f"CIM FAILED: {e}")

    log("\n=== DONE ===")
