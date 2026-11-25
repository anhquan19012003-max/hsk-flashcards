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
        check("level list shows HSK 2, 3, 4, 5 in order", levels == ["HSK 2", "HSK 3", "HSK 4", "HSK 5"], str(levels))
        check("HSK 2 row counts its 7 questions", "7 câu" in page.locator(".level-btn").first.inner_text(), page.locator(".level-btn").first.inner_text())
        check("HSK 3 row counts its 6 questions", "6 câu" in page.locator(".level-btn").nth(1).inner_text(), page.locator(".level-btn").nth(1).inner_text())

        # ---- download: one main button, plus one per level
        main_btn = page.get_by_role("button", name="Tải toàn bộ đề về máy")
        check("exactly one 'Tải toàn bộ đề về máy' button", main_btn.count() == 1)
        check("per-level buttons for HSK 2, 3, 4 and 5", all(page.get_by_role("button", name=f"Chỉ tải HSK {n}").is_visible() for n in (2, 3, 4, 5)))
        check("per-level buttons show their own size", "MB" in page.get_by_role("button", name="Chỉ tải HSK 3").inner_text())
        page.get_by_role("button", name="Chỉ tải HSK 3").click()
        check("level dialog names HSK 3", page.get_by_text("Tải đề HSK 3 về máy?").is_visible())
        page.locator("#modal-root button.primary").click()
        page.get_by_text("HSK 3 đã tải ✓").wait_for(timeout=15000)
        check("after the HSK 3 download its button says 'đã tải ✓'", True)
        check("HSK 4 can still be downloaded on its own", page.get_by_role("button", name="Chỉ tải HSK 4").is_visible() and main_btn.is_visible())

        # ---- HSK 2: no Sắp xếp câu tab, picture as the prompt of a true/false item, passage + true/false in Đọc
        page.locator("button[data-action=bank-level][data-level='2']").click()
        tabs2 = page.locator(".bank-tabs button").all_inner_texts()
        check("HSK 2 shows only the Nghe and Đọc tabs", tabs2 == ["Nghe", "Đọc"], str(tabs2))
        check("HSK 2 opens on the first tab it has", page.locator(".bank-tabs button[aria-pressed=true]").inner_text() == "Nghe")
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-chip][data-type=tf]").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        check("picture true/false: two units of one question", page.locator(".top .title").inner_text() == "Câu 1 / 2", page.locator(".top .title").inner_text())
        page.wait_for_function("document.querySelectorAll('img.bank-img.ctx[src]').length === 1 && document.querySelector('img.bank-img.ctx').naturalWidth > 0")
        check("the picture is the prompt: shown, decrypted, no printed statement",
              page.evaluate("document.querySelector('img.bank-img.ctx').naturalWidth > 0") and page.locator(".qcard .prompt").count() == 0)
        check("picture true/false has the two answer buttons ✓ / ✗", page.locator(".qcard .opt.tf").count() == 2 and page.locator(".qcard .audio-bar").count() == 1)
        # The session order is shuffled: L1 (answer ✓, has an explanation) and L2 (answer ✗) can come in either order.
        # Answer "Đúng" on both and check each against its own key.
        graded = {}
        for _ in range(2):
            page.locator(".qcard .opt.tf", has_text="Đúng").click()
            page.locator(".qcard .fb").wait_for()
            fb = page.locator(".qcard .fb").inner_text()
            graded["L1" if "hình tròn" in fb else "L2"] = fb
            if len(graded) < 2:
                page.locator("button[data-action=bank-next]").click()
        check("picture true/false: grading and script feedback", "✅ Đúng" in graded.get("L1", "") and "这是一个圆" in graded.get("L1", ""), str(graded))
        check("picture true/false: wrong answer is marked", "❌ Chưa đúng" in graded.get("L2", ""), str(graded))
        page.locator("button[data-action=bank-next]").click()
        page.get_by_role("button", name="Về danh sách").click()
        page.locator("button[data-action=bank-chip][data-type=tf]").click()  # clear the filter again (filters are kept per tab)
        page.locator("button[data-action=bank-tab][data-tab=doc]").click()
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        seen_pic = seen_tf = False
        for _ in range(2):
            if page.locator(".picbank").count():
                seen_pic = True
                check("sentence -> picture matching shows its instruction and three pictures", page.get_by_text("Chọn hình phù hợp").is_visible() and page.locator(".picbank .pic").count() == 3)
                check("sentence -> picture matching: letter buttons and sentence prompts", page.locator(".qcard").first.locator(".opt .t").count() == 0 and "圆" in page.locator(".qcard .prompt").first.inner_text())
                page.locator(".qcard").first.locator(".opt", has_text="A").click()
                page.locator(".qcard").nth(1).locator(".opt", has_text="B").click()
            else:
                seen_tf = True
                check("reading true/false shows the passage above the statement", page.locator("#bank-passage").is_visible() and "三十分钟" in page.locator("#bank-passage").inner_text() and page.locator(".qcard .prompt").count() == 1)
                page.locator(".qcard .opt.tf", has_text="Đúng").click()
            page.locator("button[data-action=bank-next]").click()
            if page.get_by_text("Hoàn thành!").count():
                break
        check("both HSK 2 reading shapes were shown", seen_pic and seen_tf)
        page.get_by_role("button", name="Về danh sách").click()
        page.get_by_label("Quay lại").first.click()

        # ---- Nghe, picture matching
        open_level(page, 3, "nghe")
        title = page.locator(".top .title").inner_text()
        check("picture unit: one unit of two questions", title == "Câu 1–2 / 2", title)
        pics = page.locator(".picbank .pic")
        check("three pictures listed once, with letters", pics.count() == 3 and page.locator(".picbank .pk").all_inner_texts() == ["A", "B", "C"])
        page.wait_for_function("document.querySelectorAll('.picbank img[src]').length === 3")
        try:  # src is set before the image has decoded: wait for the decode instead of reading naturalWidth once
            page.wait_for_function("[...document.querySelectorAll('.picbank img')].every(i => i.complete && i.naturalWidth > 0)", timeout=5000)
        except Exception:
            pass
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

        # ---- HSK 5: cloze passage and long passage with several questions
        page.get_by_label("Quay lại").first.click()  # HSK 4 level screen -> Luyện đề list
        page.locator("button[data-action=bank-level][data-level='5']").click()
        page.locator("button[data-action=bank-tab][data-tab=doc]").click()
        page.locator("button[data-action=bank-size][data-value='0']").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        seen = {"cloze": False, "long": False, "single": False}
        for _ in range(3):
            cards = page.locator(".qcard")
            n = cards.count()
            check(f"HSK 5 unit with {n} question(s) shows its passage", page.locator("#bank-passage").is_visible())
            if n > 1:
                check("every question of a passage has 'Xem lại bài đọc'", page.locator(".qcard .linkbtn").count() == n and cards.first.locator(".linkbtn").bounding_box()["height"] >= 44)
                prompts = [c.locator(".prompt").inner_text().strip() for c in cards.all()]
                if prompts[0].startswith("（"):
                    seen["cloze"] = True
                    check("cloze questions are labelled （1）（2）…", prompts == ["（1）", "（2）", "（3）"], str(prompts))
                    check("cloze passage shows the numbered blanks", "（1）" in page.locator("#bank-passage").inner_text())
                else:
                    seen["long"] = True
                last = cards.nth(n - 1)
                last.scroll_into_view_if_needed()
                last.locator(".linkbtn").click()
                page.wait_for_function("document.getElementById('bank-passage').getBoundingClientRect().top >= -2 && document.getElementById('bank-passage').getBoundingClientRect().top < 300")
                check("tapping the link scrolls back to the passage", True)
            else:
                seen["single"] = True
                check("a single-question text has no 'Xem lại' link", page.locator(".linkbtn").count() == 0)
            for c in cards.all():
                c.locator(".opt").first.click()
            page.locator("button[data-action=bank-next]").click()
            if page.get_by_text("Hoàn thành!").count():
                break
        check("all three HSK 5 reading shapes were shown", all(seen.values()), str(seen))
        page.get_by_role("button", name="Về danh sách").click()
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
