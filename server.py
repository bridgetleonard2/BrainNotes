"""BrainNotes local server.

Serves BrainNotes.html, saves notes.json, and regenerates BrainNotes.bib
from the papers in notes.json on every save. Standard library only.
Started by BrainNotes.bat (Windows) or BrainNotes.command (Mac).
Close the console window to stop it.

Where notes are saved: set "notes_dir" in config.json (see
config.example.json). Without a config, notes go in ./notes/.
"""
import json
import os
import shutil
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

def arg(name, default=None):
    """Optional command-line flags: --notes DIR, --port N, --no-browser."""
    if name in sys.argv:
        i = sys.argv.index(name)
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else default
    return default


HOST, PORT = "127.0.0.1", int(arg("--port", 8765))
ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ROOT, "config.json")


def notes_dir():
    if arg("--notes"):
        return os.path.abspath(os.path.expanduser(arg("--notes")))
    path = "notes"
    if os.path.exists(CONFIG):
        try:
            with open(CONFIG, encoding="utf-8") as f:
                path = json.load(f).get("notes_dir") or path
        except Exception as e:
            sys.exit(f"Couldn't read config.json: {e}")
    path = os.path.expandvars(os.path.expanduser(path))
    return os.path.abspath(os.path.join(ROOT, path))  # relative paths are relative to this folder


DATA = notes_dir()
NOTES = os.path.join(DATA, "notes.json")
BACKUP = os.path.join(DATA, "notes.backup.json")
BIB = os.path.join(DATA, "BrainNotes.bib")
URL = f"http://localhost:{PORT}/BrainNotes.html"
EMPTY = {"version": 1, "papers": [], "nodes": []}


def write_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def write_bib(data):
    papers = sorted(data.get("papers", []), key=lambda p: p.get("key", "").lower())
    head = (
        f"% BrainNotes bibliography: generated automatically, do not edit by hand.\n"
        f"% {len(papers)} entries, updated {datetime.now():%Y-%m-%d %H:%M}\n\n"
    )
    body = "\n\n".join(p.get("bibtex", "").strip() for p in papers if p.get("bibtex"))
    write_atomic(BIB, head + body + ("\n" if body else ""))


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".html": "text/html",
        ".json": "application/json",
        ".mz3": "application/octet-stream",
        ".bib": "text/plain; charset=utf-8",
    }

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):  # keep the console quiet
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/BrainNotes.html")
            self.end_headers()
        elif url.path == "/api/notes":
            try:
                with open(NOTES, encoding="utf-8") as f:
                    self.send_json(json.load(f))
            except FileNotFoundError:
                self.send_json(EMPTY)
        elif url.path == "/BrainNotes.bib":  # the bib lives in the notes folder
            try:
                with open(BIB, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self.send_error(404)
        elif url.path == "/api/doi":
            self.lookup_doi(urllib.parse.parse_qs(url.query).get("d", [""])[0])
        else:
            super().do_GET()

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/api/notes":
            return self.send_json({"error": "not found"}, 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(data, dict) or "nodes" not in data or "papers" not in data:
                raise ValueError("bad payload")
            if os.path.exists(NOTES):
                shutil.copyfile(NOTES, BACKUP)
            write_atomic(NOTES, json.dumps(data, indent=2, ensure_ascii=False))
            write_bib(data)
            self.send_json({"ok": True, "saved": datetime.now().isoformat(timespec="seconds")})
        except Exception as e:  # report, never crash the server
            self.send_json({"error": str(e)}, 400)

    def lookup_doi(self, doi):
        doi = doi.strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
            if doi.lower().startswith(prefix):
                doi = doi[len(prefix):]
        if not doi.startswith("10."):
            return self.send_json({"error": "That doesn't look like a DOI (should start with 10.)"}, 400)
        req = urllib.request.Request(
            "https://doi.org/" + urllib.parse.quote(doi, safe="/:;()._-"),
            headers={"Accept": "application/x-bibtex; charset=utf-8", "User-Agent": "BrainNotes/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                text = r.read().decode("utf-8", errors="replace")
            if not text.lstrip().startswith("@"):
                raise ValueError("No BibTeX returned for that DOI")
            self.send_json({"bibtex": text.strip(), "doi": doi})
        except urllib.error.HTTPError as e:
            self.send_json({"error": f"DOI not found ({e.code})"}, 404)
        except Exception as e:
            self.send_json({"error": f"Lookup failed: {e}"}, 502)


def already_running():
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex((HOST, PORT)) == 0


if __name__ == "__main__":
    if already_running():  # BrainNotes is already open: just show it
        print("BrainNotes is already running at", URL)
        if "--no-browser" not in sys.argv:
            webbrowser.open(URL)
        sys.exit(0)
    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(NOTES):
        write_atomic(NOTES, json.dumps(EMPTY, indent=2))
    if not os.path.exists(BIB):
        write_bib(EMPTY)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("BrainNotes is running at", URL)
    print("Notes are saved in", DATA)
    print("Keep this window open while you work. Close it to stop BrainNotes.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(URL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
