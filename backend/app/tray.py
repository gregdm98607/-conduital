"""
System tray integration for packaged Conduital.

Uses pystray to create a Windows system tray icon with menu options.
Falls back gracefully if pystray is not available (e.g., in development).
"""

import logging
import sys
import threading
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_icon_image():
    """Load the application icon for the system tray.

    Tries multiple locations: bundled assets (PyInstaller), then project assets.
    Falls back to a generated placeholder if no icon file is found.
    """
    try:
        from PIL import Image

        # Check for bundled icon (PyInstaller _MEIPASS)
        if getattr(sys, "frozen", False):
            icon_path = Path(sys._MEIPASS) / "assets" / "conduital.ico"
            if icon_path.exists():
                return Image.open(icon_path)

        # Check project assets directory
        assets_dir = Path(__file__).resolve().parent.parent.parent / "assets"
        for name in ("conduital.ico", "conduital.png", "icon.ico", "icon.png"):
            icon_path = assets_dir / name
            if icon_path.exists():
                return Image.open(icon_path)

        # Generate a simple placeholder icon (blue square with "C")
        img = Image.new("RGBA", (64, 64), (59, 130, 246, 255))
        try:
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)
            draw.text((20, 10), "C", fill=(255, 255, 255, 255))
        except ImportError:
            pass
        return img

    except ImportError:
        return None


def create_tray(port: int, version: str, shutdown_event: threading.Event):
    """Create and run the system tray icon.

    This function blocks until the tray is stopped (via Quit menu or shutdown_event).

    Args:
        port: The port the server is running on.
        version: Application version string.
        shutdown_event: Event to signal when the user requests quit.
    """
    try:
        import pystray
    except ImportError:
        logger.warning("pystray not available — running without system tray")
        # Block until shutdown is requested
        shutdown_event.wait()
        return

    image = _get_icon_image()
    if image is None:
        logger.warning("Could not load tray icon — running without system tray")
        shutdown_event.wait()
        return

    url = f"http://127.0.0.1:{port}"

    def open_app(_icon, _item):
        webbrowser.open(url)

    def open_settings(_icon, _item):
        webbrowser.open(f"{url}/settings")

    def quit_app(icon, _item):
        logger.info("Quit requested from system tray")
        icon.stop()
        shutdown_event.set()

    menu = pystray.Menu(
        pystray.MenuItem("Open Conduital", open_app, default=True),
        pystray.MenuItem("Settings", open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f"v{version}", None, enabled=False),
        pystray.MenuItem("Quit", quit_app),
    )

    icon = pystray.Icon("Conduital", image, "Conduital", menu)

    logger.info("System tray icon started")
    icon.run()
