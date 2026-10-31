"""Playwright test: the app tells the user when a new version was installed while it is open, and shows its version in Cài đặt.

Usage: python scripts/test_update_bar.py
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser import DOCS, launch, serve  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def real_update_check(p):
    """End to end: a page controlled by service-worker version N sees version N+1 being published and offers the update."""
    import functools
    import http.server
    import threading

    state = {"bump": False}
    sw_src = (DOCS / "sw.js").read_text(encoding="utf-8")

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0].endswith("/sw.js"):
                body = sw_src.replace('const VERSION = "', 'const VERSION = "x' if state["bump"] else 'const VERSION = "').encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def log_message(self, *a, **k):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(DOCS)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    browser = launch(p)
    page = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
    page.goto(url)
    page.evaluate("navigator.serviceWorker.ready.then(() => true)")
    page.reload()
    page.wait_for_function("!!navigator.serviceWorker.controller")
    check("real update: no bar before a new version exists", page.locator("#update-bar").count() == 0)
    state["bump"] = True  # "deploy" a new sw.js
    page.evaluate("navigator.serviceWorker.getRegistration().then((r) => r.update())")
    page.locator("#update-bar").wait_for(timeout=15000)
    check("real update: a freshly published version makes the bar appear in the open page", page.locator("#update-bar").is_visible())
    browser.close()
    srv.shutdown()


def main():
    sw_version = re.search(r'const VERSION = "(\d+)"', (DOCS / "sw.js").read_text(encoding="utf-8")).group(1)
    app_version = re.search(r'const APP_VERSION = "(\d+)"', (DOCS / "app.js").read_text(encoding="utf-8")).group(1)
    check("app.js APP_VERSION equals the service-worker VERSION (bump_version.py keeps them together)", sw_version == app_version, f"{sw_version} vs {app_version}")

    srv, url = serve(False)
    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        # first visit: a controller change is the first install, not an update -> no bar
        page.evaluate("navigator.serviceWorker.dispatchEvent(new Event('controllerchange'))")
        check("no update bar on the very first visit", page.locator("#update-bar").count() == 0)

        page.reload()  # now the page is controlled by the service worker, like every later visit
        page.wait_for_function("!!navigator.serviceWorker.controller")
        check("no update bar while nothing changed", page.locator("#update-bar").count() == 0)
        page.evaluate("navigator.serviceWorker.dispatchEvent(new Event('controllerchange'))")
        bar = page.locator("#update-bar")
        check("update bar appears when a new version takes over", bar.is_visible() and "cập nhật" in bar.inner_text().lower())
        box = bar.locator("button").bounding_box()
        check("update button is a big tap target", box["height"] >= 44 and box["width"] >= 100, str(box))
        page.evaluate("navigator.serviceWorker.dispatchEvent(new Event('controllerchange'))")
        check("the bar is not added twice", page.locator("#update-bar").count() == 1)
        page.evaluate("window.__beforeReload = true")
        with page.expect_navigation():
            bar.locator("button").click()
        check("tapping it reloads the page (fresh code)", page.evaluate("window.__beforeReload === undefined") and page.locator("#update-bar").count() == 0)

        page.get_by_role("button", name="Cài đặt").click()
        page.locator("#app-version").wait_for()
        check("Cài đặt shows the app version", page.locator("#app-version").inner_text().strip() == f"Phiên bản ứng dụng: {app_version}", page.locator("#app-version").inner_text())
        check("no page errors", not errors, str(errors))
        browser.close()
        real_update_check(p)
    srv.shutdown()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    sys.exit(1 if bad else 0)


main()
