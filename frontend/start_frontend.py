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


def run_server():
    os.chdir(FRONTEND_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    # Allow address reuse to prevent 'Address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("=" * 60)
        print(f"  TEST FRONTEND RUNNING AT: http://localhost:{PORT}")
        print("  Press Ctrl+C to stop.")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down frontend server.")


if __name__ == "__main__":
    run_server()
