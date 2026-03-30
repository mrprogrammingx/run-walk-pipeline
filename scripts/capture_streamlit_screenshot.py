#!/usr/bin/env python3
"""Capture a screenshot of the Streamlit dashboard using Playwright.

This script will:
 - start the Streamlit app in a background process
 - wait for the web UI to become available
 - open the page with Playwright and capture a full-page PNG to docs/screenshot.png
 - terminate the Streamlit process

Requirements:
 - Python packages: playwright
 - Install browser binaries: `playwright install`

Usage:
  python scripts/capture_streamlit_screenshot.py

Notes:
 - Run this from the repository root. Make sure your virtualenv is activated
   and dependencies are installed (including streamlit and playwright).
 - The script uses port 8501 by default; change PORT below if needed.
"""

import subprocess
import time
import os
import signal
import socket
from contextlib import closing

PORT = int(os.environ.get("STREAMLIT_PORT", 8501))
URL = f"http://127.0.0.1:{PORT}"
OUT_PATH = os.path.join("docs", "screenshot.png")


def wait_for_port(port, host="127.0.0.1", timeout=30.0):
    """Wait until a TCP port is open on host, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.settimeout(1.0)
                sock.connect((host, port))
                return True
            except Exception:
                time.sleep(0.5)
    return False


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    # Start Streamlit in a background process
    cmd = ["streamlit", "run", "dashboard/streamlit_app.py", "--server.port", str(PORT)]
    print("Starting Streamlit:", " ".join(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

    try:
        print("Waiting for Streamlit to start...")
        if not wait_for_port(PORT, timeout=30.0):
            raise RuntimeError("Streamlit did not start within timeout")

        print("Streamlit is up; capturing screenshot with Playwright")

        # Import Playwright here so the script can be used even if Playwright isn't installed
        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise RuntimeError("Playwright not installed. Install with: pip install playwright && playwright install") from exc

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(URL, wait_until="networkidle")
            # wait a bit for Streamlit widgets to render
            time.sleep(1.0)
            # capture full page
            page.screenshot(path=OUT_PATH, full_page=True)
            browser.close()

        print(f"Screenshot saved to {OUT_PATH}")

    finally:
        # Terminate Streamlit process group
        try:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass


if __name__ == "__main__":
    main()
