import os, sys, subprocess, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("sys_test.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    # Find Brave
    log("=== BRAVE SEARCH ===")
    brave_paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]
    for p in brave_paths:
        log(f"  {p}: {os.path.exists(p)}")

    # Search registry for Brave
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\brave.exe' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty '(default)'"],
        capture_output=True, text=True, timeout=5
    )
    log(f"Registry brave path: '{r.stdout.strip()}'")

    # Default browser
    r2 = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice' -ErrorAction SilentlyContinue).ProgId"],
        capture_output=True, text=True, timeout=5
    )
    log(f"Default browser: '{r2.stdout.strip()}'")

    # Find brave via where
    r3 = subprocess.run(["where", "brave.exe"], capture_output=True, text=True)
    log(f"where brave.exe: '{r3.stdout.strip()}'")

    # Glob search
    for pattern in [r"C:\Program Files*\BraveSoftware\**\brave.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\**\brave.exe")]:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            log(f"Glob found: {matches[0]}")

    log("\n=== UNLOCK TEST ===")
    # Test if SendKeys works on lock screen
    import ctypes
    # Check if screen is locked
    r4 = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process logonui -ErrorAction SilentlyContinue) -ne $null"],
        capture_output=True, text=True, timeout=5
    )
    log(f"Lock screen active (logonui running): {r4.stdout.strip()}")

    # Test keyboard simulation
    r5 = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('a'); Write-Host 'SendKeys OK'"],
        capture_output=True, text=True, timeout=5
    )
    log(f"SendKeys test: {r5.stdout.strip()} err={r5.stderr.strip()[:100]}")
