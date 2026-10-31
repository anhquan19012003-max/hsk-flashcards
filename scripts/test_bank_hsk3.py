"""Playwright test of the Phase 10 bank changes (two levels, picture matching, sentence matching, per-level download),
at 390x844 and 360x640, using the made-up two-level fixture bank scripts/fixtures/bank-hsk3 (never real content).

Usage: python scripts/test_bank_hsk3.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser import ROOT, launch, serve  # noqa: E402

BANK3 = ROOT / "scripts" / "fixtures" / "bank-hsk3"
RESULTS = []
PASSWORD = "test-password"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def open_level(page, level, tab, chip=None):
    page.locator(f"button[data-action=bank-level][data-level='{level}']").click()
    page.locator(f"button[data-action=bank-tab][data-tab={tab}]").click()
    page.locator("button[data-action=bank-size][data-value='0']").click()
    if chip:
        page.locator(f"button[data-action=bank-chip][data-type={chip}]").click()
    page.locator("button[data-action=bank-start][data-mode=new]").click()


def main():
    srv, url = serve(BANK3)
    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ---- unlock; two levels, HSK 3 first
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page.reload()
        page.locator("button.bank-btn").click()
        page.locator("#bank-pw").fill(PASSWORD)
        page.get_by_role("button", name="Mở khóa").click()
        page.locator(".level-btn").first.wait_for()
        levels = page.locator(".level-btn .lv").all_inner_texts()
        check("level list shows HSK 3 then HSK 4", levels == ["HSK 3", "HSK 4"], str(levels))
        check("HSK 3 row counts its 6 questions", "6 câu" in page.locator(".level-btn").first.inner_text(), page.locator(".level-btn").first.inner_text())

        # ---- download: one main button, plus one per level
        main_btn = page.get_by_role("button", name="Tải toàn bộ đề về máy")
        check("exactly one 'Tải toàn bộ đề về máy' button", main_btn.count() == 1)
        check("per-level buttons for HSK 3 and HSK 4", page.get_by_role("button", name="Chỉ tải HSK 3").is_visible() and page.get_by_role("button", name="Chỉ tải HSK 4").is_visible())
        check("per-level buttons show their own size", "MB" in page.get_by_role("button", name="Chỉ tải HSK 3").inner_text())
        page.get_by_role("button", name="Chỉ tải HSK 3").click()
        check("level dialog names HSK 3", page.get_by_text("Tải đề HSK 3 về máy?").is_visible())
        page.locator("#modal-root button.primary").click()
        page.get_by_text("HSK 3 đã tải ✓").wait_for(timeout=15000)
        check("after the HSK 3 download its button says 'đã tải ✓'", True)
        check("HSK 4 can still be downloaded on its own", page.get_by_role("button", name="Chỉ tải HSK 4").is_visible() and main_btn.is_visible())

        # ---- Nghe, picture matching
        open_level(page, 3, "nghe")
        title = page.locator(".top .title").inner_text()
        check("picture unit: one unit of two questions", title == "Câu 1–2 / 2", title)
        pics = page.locator(".picbank .pic")
        check("three pictures listed once, with letters", pics.count() == 3 and page.locator(".picbank .pk").all_inner_texts() == ["A", "B", "C"])
        page.wait_for_function("document.querySelectorAll('.picbank img[src]').length === 3")
        check("pictures are decrypted and shown", page.evaluate("[...document.querySelectorAll('.picbank img')].every(i => i.naturalWidth > 0)"))
        check("each question has its own audio bar", page.locator(".qcard .audio-bar").count() == 2)
        first = page.locator(".qcard").first
        check("options are letter buttons only (no repeated pictures)", first.locator(".opt").count() == 3 and first.locator(".opt img").count() == 0 and first.locator(".opt .t").count() == 0)
        boxes = [b.bounding_box() for b in first.locator(".opt").all()]
        check("letter buttons are at least 44 px", all(b["width"] >= 44 and b["height"] >= 44 for b in boxes), str(boxes))
        pics.first.click()
        page.locator(".zoom img").wait_for()
        check("tap on a picture enlarges it", page.locator(".zoom img").is_visible() and page.locator(".zoom img").bounding_box()["width"] > 200)
        page.locator(".zoom").click()
        check("tap closes the enlarged picture", page.locator(".zoom").count() == 0)
        # first question's answer is B; pick A (wrong)
        first.locator(".opt", has_text="A").click()
        check("wrong answer: the correct picture is shown in the feedback", first.locator(".fb-pic img").count() == 1 and "hình B" in first.locator(".fb-pic").inner_text())
        check("explanation shown, no Chinese-explanation toggle (explain_zh empty)", "Hộp vuông" in first.locator(".fb").inner_text() and first.locator(".expl-zh").count() == 0)
        check("listening script shown after answering", "方的盒子" in first.locator(".fb").inner_text())
        page.locator(".qcard").nth(1).locator(".opt", has_text="A").click()
        page.locator("button[data-action=bank-next]").click()
        check("set summary after the unit", page.get_by_text("Hoàn thành!").is_visible())
        page.get_by_role("button", name="Về danh sách").click()

        # ---- Đọc, sentence matching + word bank
        page.locator("button[data-action=bank-tab][data-tab=doc]").click()
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        seen_sent = seen_words = False
        answers = {"我去邮局寄信。": "B", "他正在写作业。": "C", "她学习非常 ( )。": "C"}
        for _ in range(3):
            if page.locator(".sentlist").count():
                seen_sent = True
                check("sentence matching shows the instruction", page.get_by_text("Chọn câu phù hợp").is_visible())
                check("three sentences listed once with letters", page.locator(".sentlist .sl").count() == 3)
                check("options are letters only", page.locator(".qcard").first.locator(".opt .t").count() == 0)
                check("sentence matching: no overflow at 390 px", page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
            elif page.locator(".wordlist").count():
                seen_words = True
                check("plain word bank keeps its word buttons", page.locator(".qcard .opt .t").count() >= 3)
            for card in page.locator(".qcard").all():
                prompt = card.locator(".prompt").inner_text().strip()
                card.locator(".opt", has_text=answers[prompt]).first.click()
            page.locator("button[data-action=bank-next]").click()
            if page.get_by_text("Hoàn thành!").count():
                break
        check("both layouts were shown in Đọc", seen_sent and seen_words)
        page.get_by_role("button", name="Về danh sách").click()

        # ---- Sắp xếp still works in level 3
        page.locator("button[data-action=bank-tab][data-tab=sapxep]").click()
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        for word in ["他", "身体", "有点儿", "不舒服"]:
            page.locator(".tiles .tile:not(.used)", has_text=word).first.click()
        page.get_by_role("button", name="Kiểm tra").click()
        check("order-words in HSK 3 grades correctly", page.get_by_text("✅ Đúng").is_visible())
        page.locator("button[data-action=bank-next]").click()
        page.get_by_role("button", name="Về danh sách").click()

        # ---- HSK 4 unchanged
        page.get_by_label("Quay lại").first.click()
        page.locator("button[data-action=bank-level][data-level='4']").click()
        page.locator("button[data-action=bank-tab][data-tab=nghe]").click()
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        check("HSK 4 listening still shows its plain question cards", page.locator(".qcard").count() >= 1 and page.locator(".picbank").count() == 0)
        page.get_by_label("Quay lại").first.click()

        # ---- phone width 360x640
        small = browser.new_context(viewport={"width": 360, "height": 640})
        sp = small.new_page()
        sp.on("pageerror", lambda e: errors.append(str(e)))
        sp.goto(url)
        sp.locator("button.bank-btn").click()
        sp.locator("#bank-pw").fill(PASSWORD)
        sp.get_by_role("button", name="Mở khóa").click()
        sp.locator(".level-btn").first.wait_for()
        open_level(sp, 3, "nghe")
        sp.wait_for_function("document.querySelectorAll('.picbank img[src]').length === 3")
        boxes = [b.bounding_box() for b in sp.locator(".picbank .pic").all()]
        check("360 px: three pictures per row, each at least 90 px wide", len({round(b["y"]) for b in boxes}) == 1 and all(b["width"] >= 90 for b in boxes), str(boxes))
        check("360 px: letter badges readable", sp.locator(".picbank .pk").first.bounding_box()["height"] >= 24)
        check("360 px: no horizontal overflow", sp.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))
        lb = [b.bounding_box() for b in sp.locator(".qcard").first.locator(".opt").all()]
        check("360 px: letter buttons at least 44 px", all(b["width"] >= 44 and b["height"] >= 44 for b in lb), str(lb))
        sp.locator(".picbank .pic").nth(2).click()
        check("360 px: zoom works", sp.locator(".zoom img").is_visible())
        small.close()

        check("no page errors", not errors, str(errors))
        browser.close()
    srv.shutdown()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    sys.exit(1 if bad else 0)


main()
