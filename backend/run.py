#!/usr/bin/env python3
"""
Project Tracker — Single-Process Launcher

Starts the full application:
1. Ensures database directory exists
2. Runs Alembic migrations
3. Starts Uvicorn (FastAPI + static frontend)
4. Opens the default browser
5. Handles clean shutdown

Usage:
    python run.py
    python run.py --port 8080
    python run.py --no-browser
"""

import argparse
import logging
import os
import signal
import socket
import sys
import threading
import time
import webbrowser

import uvicorn


def find_available_port(start_port: int = 52140, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")


def open_browser_delayed(url: str, delay: float = 1.5):
    """Open the browser after a short delay (give server time to start)."""
    def _open():
        time.sleep(delay)
        webbrowser.open(url)
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def main():
    parser = argparse.ArgumentParser(description="Project Tracker Launcher")
    parser.add_argument("--port", type=int, default=None, help="Port to run on (default: auto-detect from 52140)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser on startup")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with auto-reload")
    args = parser.parse_args()

    # Find available port
    port = args.port or find_available_port()

    # Set port in environment so FastAPI config picks it up
    os.environ.setdefault("SERVER_PORT", str(port))
    os.environ.setdefault("SERVER_HOST", args.host)

    url = f"http://{args.host}:{port}"

    print(f"\n  Project Tracker v1.0.0-alpha")
    print(f"  {'─' * 36}")
    print(f"  Server:  {url}")
    print(f"  Docs:    {url}/docs")
    print(f"  Health:  {url}/health")
    print(f"  {'─' * 36}")
    print(f"  Press Ctrl+C to stop\n")

    # Open browser unless --no-browser
    if not args.no_browser:
        open_browser_delayed(url)

    # Run Uvicorn
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=port,
            reload=args.debug,
            log_level="info" if not args.debug else "debug",
        )
    except KeyboardInterrupt:
        print("\n  Shutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()
