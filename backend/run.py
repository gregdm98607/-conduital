#!/usr/bin/env python3
"""
Conduital — Single-Process Launcher

Starts the full application:
1. Ensures database directory exists
2. Runs Alembic migrations
3. Starts Uvicorn (FastAPI + static frontend)
4. Opens the default browser
5. Handles clean shutdown

Development mode: console output, auto-reload support, no system tray.
Packaged mode (PyInstaller): no console, system tray icon, browser auto-open.

Usage:
    python run.py
    python run.py --port 8080
    python run.py --no-browser
"""

import argparse
import logging
import os
import socket
import sys
import threading
import time
import webbrowser

# When packaged with PyInstaller, ensure the bundle dir is on sys.path
# and set CWD so relative imports and data file resolution work.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _bundle_dir = sys._MEIPASS
    if _bundle_dir not in sys.path:
        sys.path.insert(0, _bundle_dir)
    os.chdir(_bundle_dir)

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


def run_development(args, port: int, version: str):
    """Run in development mode — console output, optional auto-reload."""
    url = f"http://{args.host}:{port}"

    print(f"\n  Conduital v{version}")
    print(f"  {'-' * 36}")
    print(f"  Server:  {url}")
    print(f"  Docs:    {url}/docs")
    print(f"  Health:  {url}/health")
    print(f"  {'-' * 36}")
    print(f"  Press Ctrl+C to stop\n")

    if not args.no_browser:
        open_browser_delayed(url)

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


def run_packaged(port: int, version: str):
    """Run in packaged mode — system tray icon, no console window."""
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    os.environ.setdefault("SERVER_PORT", str(port))
    os.environ.setdefault("SERVER_HOST", host)

    # Use the shared shutdown event so the /api/v1/shutdown endpoint,
    # system tray quit, and installer can all trigger the same event.
    from app.core.shutdown import shutdown_event

    # Start Uvicorn in a background thread
    # log_config=None prevents uvicorn from loading its default LOGGING_CONFIG
    # which uses color formatters that call sys.stderr.isatty() — this fails
    # in PyInstaller bundles with console=False. Our app.core.logging_config
    # handles all logging instead.
    server_config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        log_config=None,
    )
    server = uvicorn.Server(server_config)

    def run_server():
        server.run()
        # If server exits (error or shutdown), signal tray to stop
        shutdown_event.set()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Open browser
    open_browser_delayed(url, delay=2.0)

    # Run system tray (blocks until quit)
    try:
        from app.tray import create_tray
        create_tray(port, version, shutdown_event)
    except Exception:
        # If tray fails, just wait for shutdown signal or Ctrl+C
        try:
            shutdown_event.wait()
        except KeyboardInterrupt:
            pass

    # Request server shutdown
    server.should_exit = True
    server_thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description="Conduital Launcher")
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

    # Read version from config (single source of truth)
    from app.core.config import settings
    version = settings.VERSION

    # Choose execution mode
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        run_packaged(port, version)
    else:
        run_development(args, port, version)


if __name__ == "__main__":
    main()
