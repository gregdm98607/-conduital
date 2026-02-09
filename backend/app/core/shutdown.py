"""Graceful shutdown coordination.

Provides a shared shutdown event that can be triggered from:
- System tray Quit button
- /api/v1/shutdown endpoint
- Installer pre-uninstall
"""

import threading

# Global shutdown event -- set this to request graceful shutdown.
# In packaged mode, run.py passes this same event to create_tray()
# and monitors it to know when to stop the uvicorn server.
shutdown_event = threading.Event()
