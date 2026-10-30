"""Shared Playwright helpers for the browser tests."""
import functools
import http.server
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
FIXTURE_BANK = ROOT / "scripts" / "fixtures" / "bank"


def launch(p):
    """Default Chromium; falls back to the pre-installed one in the cloud container."""
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])


def serve(bank_dir=None, docs=DOCS):
    """Serve docs/ on a free port. /bank/... is answered from `bank_dir` (the fixture) instead of docs/bank/.
    bank_dir=False serves no bank at all (404), None serves docs/bank/ as it is."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            clean = path.split("?")[0].split("#")[0]
            if clean.startswith("/bank/") and bank_dir is not None:
                if bank_dir is False:
                    return str(docs / "__no_bank__" / clean[6:])
                return str(Path(bank_dir) / clean[6:])
            return super().translate_path(path)

        def log_message(self, *a, **k):
            pass

    handler = functools.partial(Handler, directory=str(docs))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"
