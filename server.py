"""
Wordle Web Server — uses Python's built-in http.server (no Flask needed).

Endpoints:
  GET /                  → web/index.html
  GET /style.css         → web/style.css
  GET /app.js            → web/app.js
  GET /words/stanford    → Stanford GraphBase 5-letter words (one per line)
  GET /words/sowpods     → SOWPODS 5-letter Scrabble words (one per line)

Run:
  python3 server.py
Then open: http://localhost:5000
"""

import http.server
import pathlib
import urllib.request
import urllib.error
import mimetypes

BASE_DIR = pathlib.Path(__file__).parent
WEB_DIR  = BASE_DIR / "web"

STANFORD_CACHE = BASE_DIR / "sgb-words.txt"
STANFORD_URL   = "https://www-cs-faculty.stanford.edu/~knuth/sgb-words.txt"

SOWPODS_CACHE  = BASE_DIR / "sowpods-5.txt"
SOWPODS_URL    = "https://raw.githubusercontent.com/MReeveCO/sowpods/main/sowpods.txt"

PORT = 5000


# ── Word list helpers ─────────────────────────────────────────────────────────

def ensure_stanford() -> bytes:
    if not STANFORD_CACHE.exists():
        print("  Downloading Stanford word list…", flush=True)
        with urllib.request.urlopen(STANFORD_URL, timeout=10) as resp:
            data = resp.read()
        STANFORD_CACHE.write_bytes(data)
        print(f"  Saved {STANFORD_CACHE.name}", flush=True)
    return STANFORD_CACHE.read_bytes()


def ensure_sowpods() -> bytes:
    if not SOWPODS_CACHE.exists():
        print("  Downloading SOWPODS word list…", flush=True)
        with urllib.request.urlopen(SOWPODS_URL, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
        five = [
            w.strip().lower()
            for w in raw.splitlines()
            if len(w.strip()) == 5 and w.strip().isalpha()
        ]
        content = "\n".join(five)
        SOWPODS_CACHE.write_text(content, encoding="utf-8")
        print(f"  Saved {len(five):,} SOWPODS 5-letter words to {SOWPODS_CACHE.name}", flush=True)
    return SOWPODS_CACHE.read_bytes()


# ── Request handler ───────────────────────────────────────────────────────────

class WordleHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Cleaner logs
        print(f"  {self.address_string()} → {fmt % args}", flush=True)

    def send_bytes(self, data: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]  # strip query string

        # ── Word list API ──────────────────────────────────────────
        if path == "/words/stanford":
            try:
                self.send_bytes(ensure_stanford(), "text/plain; charset=utf-8")
            except Exception as e:
                msg = f"Error: {e}".encode()
                self.send_bytes(msg, "text/plain", 500)
            return

        if path == "/words/sowpods":
            try:
                self.send_bytes(ensure_sowpods(), "text/plain; charset=utf-8")
            except Exception as e:
                msg = f"Error: {e}".encode()
                self.send_bytes(msg, "text/plain", 500)
            return

        # ── Static files ───────────────────────────────────────────
        # Map "/" to index.html
        if path == "/":
            path = "/index.html"

        file_path = WEB_DIR / path.lstrip("/")

        if not file_path.exists() or not file_path.is_file():
            self.send_bytes(b"404 Not Found", "text/plain", 404)
            return

        mime, _ = mimetypes.guess_type(str(file_path))
        mime = mime or "application/octet-stream"
        self.send_bytes(file_path.read_bytes(), mime)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Pre-cache word lists on startup so first page load is instant
    print("=" * 50)
    print("  🟩  Wordle Web App")
    print("=" * 50)
    try:
        ensure_stanford()
        ensure_sowpods()
    except Exception as e:
        print(f"  Warning: could not pre-download word lists: {e}")

    server = http.server.HTTPServer(("0.0.0.0", PORT), WordleHandler)
    print(f"\n  Server running at: http://localhost:{PORT}")
    print("  Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
