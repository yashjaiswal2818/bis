"""Lightweight Static Web Server for the Test Frontend.

Runs Python's built-in http.server on port 3000 without requiring Node.js or npm.
"""
from __future__ import annotations

import http.server
import os
import socketserver
from pathlib import Path

PORT = 3000
FRONTEND_DIR = Path(__file__).resolve().parent
DIST_DIR = FRONTEND_DIR / "dist"
SERVE_DIR = DIST_DIR if DIST_DIR.exists() else FRONTEND_DIR


class SPARequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving React SPA assets with index.html fallback."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SERVE_DIR), **kwargs)

    def do_GET(self):
        # Fallback to index.html if requested path does not exist
        path = self.translate_path(self.path)
        if not os.path.exists(path):
            self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        if self.path.endswith(".html") or self.path == "/":
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SPARequestHandler) as httpd:
        print("=" * 65)
        print(f"  REACT FRONTEND RUNNING AT: http://localhost:{PORT}")
        print(f"  Serving: {SERVE_DIR}")
        print("  Press Ctrl+C to stop.")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down frontend server.")


if __name__ == "__main__":
    run_server()
