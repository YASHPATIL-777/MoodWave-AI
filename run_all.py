"""
MoodWave - Run Server
Both Spotify and YouTube pages run from ONE server (port 5000).
Anyone on the same Wi-Fi can open using this laptop's IP.

Run:
    python run_all.py
"""

import subprocess
import sys
import os
import socket
import threading

SPOTIFY_DIR = os.path.dirname(os.path.abspath(__file__))


def get_local_ip():
    """Get this laptop's Wi-Fi / LAN IP address automatically."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def stream(proc, label):
    for line in iter(proc.stdout.readline, b""):
        try:
            print(f"[{label}] " + line.decode("utf-8", errors="replace"), end="")
        except Exception:
            pass


def launch(script_dir, script_name, label):
    script_path = os.path.join(script_dir, script_name)
    if not os.path.isfile(script_path):
        print(f"[ERROR] Script not found: {script_path}")
        return None
    proc = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=script_dir,
    )
    t = threading.Thread(target=stream, args=(proc, label), daemon=True)
    t.start()
    return proc


if __name__ == "__main__":
    local_ip = get_local_ip()

    print("=" * 62)
    print("  MoodWave - Music Player")
    print("=" * 62)
    print()
    print("  -- Access URLs ----------------------------------------")
    print(f"  [PC] Is laptop par    ->  http://localhost:5000")
    print(f"  [Mobile] Same Wi-Fi par-> http://{local_ip}:5000")
    print()
    print("  [Spotify] Spotify page->  http://localhost:5000/")
    print("  [YouTube] YouTube page->  http://localhost:5000/yt")
    print("  [Offline] Offline mode->  http://localhost:5000/offline")
    print()
    print("  [TIP] Kisi bhi doosre laptop/phone par yeh URL kholo:")
    print(f"      http://{local_ip}:5000")
    print("  [WARNING] Zaruri: Dono devices ek hi Wi-Fi se connected hon!")
    print()
    print("=" * 62)
    print()

    sp = launch(SPOTIFY_DIR, "app.py", "MoodWave:5000")
    if not sp:
        print("[ERROR] app.py not found! Check the music project folder.")
        sys.exit(1)

    print("[MoodWave] Server chal raha hai. Ctrl+C dabaao band karne ke liye.\n")

    try:
        sp.wait()
    except KeyboardInterrupt:
        print("\n[MoodWave] Server band ho raha hai...")
        sp.terminate()
        print("[MoodWave] Band ho gaya. Bye! :)")
