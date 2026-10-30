"""Render the app icons (192, 512, apple-touch 180) with Playwright. Character stays inside the maskable safe zone."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "icons"
HTML = """<html><body style="margin:0"><div style="width:512px;height:512px;background:#2457c5;display:flex;
align-items:center;justify-content:center;color:#fff;font-size:250px;font-weight:700;
font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;">汉</div></body></html>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for size, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
            page = browser.new_page(viewport={"width": 512, "height": 512}, device_scale_factor=size / 512)
            page.set_content(HTML)
            page.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": 512, "height": 512})
            page.close()
        browser.close()
    print("icons written to", OUT)


if __name__ == "__main__":
    sys.exit(main())
