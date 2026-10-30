"""Smoke test of the real docs/bank/ in a browser. Needs BANK_PASSWORD in the environment (never printed); skipped otherwise.

Usage: python scripts/test_real_bank.py
"""
import os
import sys

from playwright.sync_api import sync_playwright

from browser import launch, serve

pw = os.environ.get("BANK_PASSWORD")
if not pw:
    print("BANK_PASSWORD not set: skipped")
    sys.exit(0)

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


srv, url = serve()  # the real docs/bank
with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(url)
    page.locator("button.bank-btn").click()
    page.locator("#bank-pw").fill("sai-mat-khau")
    page.get_by_role("button", name="Mở khóa").click()
    page.get_by_text("Mật khẩu chưa đúng").wait_for()
    check("real bank: wrong password refused", True)
    page.locator("#bank-pw").fill(pw)
    page.get_by_role("button", name="Mở khóa").click()
    page.get_by_text("95 câu · Đã làm đúng 0").wait_for()
    check("real bank: unlocks, 95 questions", True)
    page.locator(".level-btn").click()
    for tab, n in (("nghe", 45), ("doc", 30), ("sapxep", 20)):
        page.locator(f"button[data-action=bank-tab][data-tab={tab}]").click()
        check(f"tab {tab}: {n} questions", page.get_by_text(f"Còn {n} câu chưa làm đúng").is_visible())
    page.locator("button[data-action=bank-tab][data-tab=nghe]").click()
    page.locator("button[data-action=bank-size][data-value='0']").click()
    page.locator("button[data-action=bank-start][data-mode=new]").click()
    played = 0
    for _ in range(45):  # play the clip of every listening unit
        page.get_by_role("button", name="▶ Nghe").first.click()
        page.wait_for_function("() => { const a = window.__hskBankPlayer; return a.src.startsWith('blob:') && a.duration > 1 && (a.currentTime > 0 || a.ended); }", timeout=8000)
        played += 1
        for card in page.locator(".qcard").all():
            card.locator("button.opt").first.click()
        page.locator("button[data-action=bank-next]").click()
        if page.get_by_text("Hoàn thành!").is_visible():
            break
    check("every listening unit's clip decrypts and plays", played == 40, str(played))
    check("no console errors", not errors, "; ".join(errors[:2]))
    browser.close()
srv.shutdown()
print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
