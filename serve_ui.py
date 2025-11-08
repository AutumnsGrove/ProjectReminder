#!/usr/bin/env python3
"""
Simple HTTP server to serve the UI for testing
Run from project root: python serve_ui.py
"""

import http.server
import socketserver
import os
from pathlib import Path

# Change to public directory
public_dir = Path(__file__).parent / "public"
os.chdir(public_dir)

PORT = 3077

Handler = http.server.SimpleHTTPRequestHandler

print(f"Starting UI server at http://localhost:{PORT}")
print(f"Serving directory: {public_dir}")
print(f"\nOpen in browser: http://localhost:{PORT}")
print("Press Ctrl+C to stop\n")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
