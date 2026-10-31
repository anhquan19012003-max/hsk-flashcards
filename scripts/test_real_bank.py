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
    page.locator(".level-btn .sub").first.wait_for()
    # per paper: (questions, Nghe, Đọc, Sắp xếp câu); HSK 3 papers skip writing part 2, HSK 4 papers skip writing part 2 too
    PER_PAPER = {3: (75, 40, 30, 5), 4: (95, 45, 30, 20)}
    rows = {int(r.locator(".lv").inner_text().split()[1]): int(r.locator(".sub").inner_text().split(" câu")[0]) for r in page.locator(".level-btn").all()}
    check(f"real bank: unlocks with levels {sorted(rows)}", bool(rows) and set(rows) <= set(PER_PAPER), str(rows))
    for level, total in sorted(rows.items()):
        per, n_nghe, n_doc, n_sx = PER_PAPER[level]
        papers = total // per
        check(f"HSK {level}: {total} questions = {papers} full papers of {per}", total % per == 0 and papers >= 1)
        page.locator(f"button[data-action=bank-level][data-level='{level}']").click()
        for tab, n in (("nghe", n_nghe * papers), ("doc", n_doc * papers), ("sapxep", n_sx * papers)):
            page.locator(f"button[data-action=bank-tab][data-tab={tab}]").click()
            check(f"HSK {level} tab {tab}: {n} questions", page.get_by_text(f"Còn {n} câu chưa làm đúng").is_visible())
        page.locator("button[data-action=bank-tab][data-tab=nghe]").click()
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        played = 0
        for _ in range(n_nghe * papers):  # every unit: play every clip it has (HSK 4 passages share one clip; HSK 3 has one per question)
            for i in range(page.get_by_role("button", name="▶ Nghe").count()):
                page.get_by_role("button", name="▶ Nghe").nth(i).click()
                page.wait_for_function("() => { const a = window.__hskBankPlayer; return a.src.startsWith('blob:') && a.duration > 1 && (a.currentTime > 0 || a.ended); }", timeout=8000)
                played += 1
            if level == 3 and page.locator(".picbank").count():  # pictures must decrypt as well
                page.wait_for_function("document.querySelectorAll('.picbank img[src]').length === document.querySelectorAll('.picbank img').length", timeout=8000)
                check(f"HSK 3 pictures decrypt (unit with {page.locator('.picbank img').count()} pictures)", page.evaluate("[...document.querySelectorAll('.picbank img')].every(i => i.naturalWidth > 0)"))
            for card in page.locator(".qcard").all():
                card.locator("button.opt").first.click()
            page.locator("button[data-action=bank-next]").click()
            if page.get_by_text("Hoàn thành!").is_visible():
                break
        check(f"HSK {level}: every listening question's clip decrypts and plays", played == 40 * papers, str(played))
        page.get_by_role("button", name="Về danh sách").click()
        page.get_by_label("Quay lại").first.click()
    check("no console errors", not errors, "; ".join(errors[:2]))
    browser.close()
srv.shutdown()
print(f"{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
