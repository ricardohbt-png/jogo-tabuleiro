#!/usr/bin/env python3
"""
Legends for Hire — Start Game
Launcher simples: o próprio server.py serve a página E o WebSocket na porta 8765,
então basta iniciar um processo.
"""

import subprocess
import sys
import time
import os
import webbrowser

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("\n" + "=" * 70)
    print("LEGENDS FOR HIRE — Starting game server")
    print("=" * 70 + "\n")

    # server.py serve página + WebSocket na MESMA porta (8765)
    print("[1] Starting server (game + WebSocket) on port 8765...")
    try:
        subprocess.Popen([sys.executable, 'server.py'])
        print("    Server started")
    except Exception as e:
        print(f"    ERROR: Could not start server: {e}")
        return

    time.sleep(2)

    url = "http://localhost:8765/index.html"
    print("\n" + "=" * 70)
    print("GAME IS READY!")
    print("=" * 70)
    print(f"\nOpen your browser and go to:\n  {url}")
    print("\nTo play over the internet, open a tunnel to port 8765, e.g.:")
    print("  cloudflared tunnel --url http://localhost:8765")
    print("  (or: ngrok http 8765)  → share the https link + /index.html")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == '__main__':
    main()
