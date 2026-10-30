"""Playwright test of Phase 9 part A (Cài đặt shows Luyện đề whenever unlocked; download shortcut) at 390x844, fixture bank only.

Usage: python scripts/test_bank_download.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser import FIXTURE_BANK, launch, serve  # noqa: E402

RESULTS = []
PASSWORD = "test-password"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def main():
    srv, url = serve(FIXTURE_BANK)
    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # locked, no saved key: no Luyện đề section in Cài đặt
        page.goto(url)
        page.get_by_role("button", name="Cài đặt").click()
        page.get_by_text("Tiến độ học").wait_for()
        check("A1 no Luyện đề section while locked", page.get_by_role("button", name="Khóa lại").count() == 0)

        # unlock, then a brand-new visit straight into Cài đặt (nothing opened before): the section must appear
        page.goto(url)
        page.locator("button.bank-btn").click()
        page.locator("#bank-pw").fill(PASSWORD)
        page.get_by_role("button", name="Mở khóa").click()
        page.locator(".level-btn").first.wait_for()
        page.goto(url)
        page.get_by_role("button", name="Cài đặt").click()
        page.get_by_role("button", name="Khóa lại").wait_for(timeout=5000)
        check("A1 Cài đặt shows Luyện đề right after a fresh visit", page.get_by_role("button", name="Tải toàn bộ đề về máy").is_visible())

        # A2: shortcut on the Luyện đề screen
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page.reload()
        page.locator("button.bank-btn").click()
        page.locator(".level-btn").first.wait_for()
        btn = page.get_by_role("button", name="Tải toàn bộ đề về máy")
        check("A2 download button below the level list", btn.is_visible())
        check("A2 shows size and Wi-Fi hint", "MB" in btn.inner_text() and "Wi-Fi" in btn.inner_text(), btn.inner_text())
        check("A2 says it is optional", page.get_by_text("Không bắt buộc").is_visible())
        btn.click()
        check("A2 dialog shows size and 'Nên dùng Wi-Fi'", page.get_by_text("Nên dùng Wi-Fi.").is_visible() and page.get_by_text("MB").first.is_visible())
        page.get_by_role("button", name="Hủy").click()
        check("A2 cancel keeps the button", btn.is_visible())
        btn.click()
        page.locator("#modal-root button.primary").click()
        page.locator("#bank-cached").wait_for(timeout=15000)
        check("A2 after downloading it says 'Đã tải về máy ✓'", "Đã tải về máy" in page.locator("#bank-cached").inner_text())
        check("A2 button is gone once everything is cached", page.get_by_role("button", name="Tải toàn bộ đề về máy").count() == 0)
        page.get_by_label("Quay lại").first.click()
        page.get_by_role("button", name="Cài đặt").click()
        page.locator("#bank-cached").wait_for(timeout=5000)
        check("A2 Cài đặt shows the same cached state", page.get_by_role("button", name="Khóa lại").is_visible())
        check("no page errors", not errors, str(errors))
        browser.close()
    srv.shutdown()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    sys.exit(1 if bad else 0)


main()
