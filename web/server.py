#!/usr/bin/env python3
"""Serve the Rafah map and proxy elevation tiles.

The public Terrarium bucket does not send browser CORS headers, so the
3D terrain is fetched here and passed through to the page.
"""

import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765
TERRAIN = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        if self.path.startswith("/terrain/"):
            self.send_header("Cache-Control", "public, max-age=86400")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        request_path = self.path.split("?", 1)[0]
        if request_path in ("/", "/index.html"):
            self.path = "/web/index.html"
        if self.path.startswith("/terrain/"):
            self.proxy_terrain()
            return
        super().do_GET()

    def proxy_terrain(self):
        tile = self.path[len("/terrain/") :].split("?", 1)[0]
        url = TERRAIN + tile
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rafah-map/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                content_type = resp.headers.get("Content-Type", "image/png")
        except Exception as exc:  # noqa: BLE001
            message = f"terrain tile failed: {exc}".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Rafah map: http://127.0.0.1:{PORT}/web/")
    server.serve_forever()
