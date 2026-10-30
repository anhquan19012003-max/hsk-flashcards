"""End-to-end test of Luyện viết (writing practice) in a 390x844 browser. Serves docs/ itself.

Usage: python scripts/test_writing.py
Real finger drawing is tested by Quan on his phone; here strokes are simulated with the mouse along the
character's `medians` (stroke centre lines) from docs/hanzi/{char}.json.
"""
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from browser import launch
from test_app import DOCS, RESULTS, check, progress, serve

WORDS = json.loads((DOCS / "data" / "hsk1.json").read_text(encoding="utf-8"))["words"]
TARGET = next(w for w in WORDS if w["hanzi"] == "爱好")  # two characters, both with stroke data
PADDING = 14  # same as docs/js/writing.js


def seed(page, target_dirs=None, others=None):
    """Mark every word except TARGET with `others` (a dict like {"zv":1,"wr":1}) so TARGET is the only word left."""
    page.evaluate(
        """([id, others]) => {
          const p = {};
          for (let i = 1; i <= 500; i++) { const k = '1-' + String(i).padStart(4, '0'); if (k !== id) p[k] = others; }
          localStorage.setItem('hskfc.v1.progress', JSON.stringify(p)); }""",
        [TARGET["id"], others or {"zv": 1, "vz": 1, "wr": 1}])


def wait_char_ready(page):
    page.locator(".wr-canvas svg").wait_for()
    page.wait_for_timeout(200)


def draw_current_char(page, ch, order=None):
    """Draw every stroke of `ch` with the mouse, following the stroke medians (in `order`, default: the correct order)."""
    data = json.loads((DOCS / "hanzi" / f"{ch}.json").read_text(encoding="utf-8"))
    box = page.locator(".wr-canvas svg").bounding_box()
    size = box["width"]
    scale = (size - 2 * PADDING) / 1024
    medians = data["medians"]
    for median in (medians[i] for i in (order or range(len(medians)))):
        pts = [(box["x"] + PADDING + x * scale, box["y"] + size - (124 * scale + PADDING) - y * scale) for x, y in median]
        page.mouse.move(*pts[0])
        page.mouse.down()
        for a, b in zip(pts, pts[1:]):
            for t in (0.25, 0.5, 0.75, 1):
                page.mouse.move(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        page.mouse.up()
        page.wait_for_timeout(120)


def main():
    srv, url = serve()
    with sync_playwright() as p:
        browser = launch(p)
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")

        # --- level screen has the new mode and the review picker lists it
        page.locator(".level-btn").first.click()
        page.get_by_text("Còn 500 từ").first.wait_for()
        check("level screen: Luyện viết button with remaining count",
              page.get_by_role("button", name="Luyện viết ✍️").is_visible() and page.get_by_text("Còn 500 từ").count() == 4)
        check("level screen: review line shows all three directions", page.get_by_text("Luyện viết: 0").is_visible())

        # --- only TARGET is left to write; a 2-character word renders two boxes + the writing area
        seed(page)
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Luyện viết ✍️").click()
        wait_char_ready(page)
        check("header 1 / 1", page.get_by_text("1 / 1").is_visible())
        check("2 character boxes", page.locator(".wr-box").count() == 2)
        area = page.locator(".wr-area").bounding_box()
        check("writing area is square and fits the screen", abs(area["width"] - area["height"]) < 1 and area["width"] <= 300 and area["x"] >= 16, str(area))
        check("prompt shows meaning and pinyin, not the hanzi",
              page.get_by_text(TARGET["meaning"]).first.is_visible() and page.locator(".wr-prompt .pinyin").inner_text() == TARGET["pinyin"]
              and TARGET["hanzi"] not in page.locator(".wr-prompt").inner_text())
        check("touch-action none on the writing area", page.locator(".wr-area").evaluate("e => getComputedStyle(e).touchAction") == "none")
        check("page overscroll disabled while writing", page.evaluate("getComputedStyle(document.documentElement).overscrollBehaviorY") == "none")
        buttons = [page.get_by_role("button", name=n) for n in ("Xem cách viết", "Hiện chữ mờ", "Viết lại", "Bỏ qua chữ này")]
        check("4 action buttons, each >= 44px high", all(b.is_visible() and b.bounding_box()["height"] >= 44 for b in buttons))

        # --- outline toggle is remembered
        page.get_by_role("button", name="Hiện chữ mờ").click()
        check("outline toggle relabels and is saved",
              page.get_by_role("button", name="Ẩn chữ mờ").is_visible()
              and page.evaluate("JSON.parse(localStorage.getItem('hskfc.v1.settings')).writingOutline") is True)
        page.get_by_role("button", name="Ẩn chữ mờ").click()

        # --- animation, then restart
        page.get_by_role("button", name="Xem cách viết").click()
        page.wait_for_function("document.querySelector('[data-wr=animate]').disabled", timeout=5000)
        page.wait_for_function("!document.querySelector('[data-wr=animate]').disabled", timeout=30000)
        page.wait_for_timeout(300)
        check("animation ends and quiz is available again", page.locator(".wr-canvas svg").is_visible())
        page.get_by_role("button", name="Viết lại").click()
        wait_char_ready(page)

        # --- skip both characters -> result line + card back + buttons
        page.get_by_role("button", name="Bỏ qua chữ này").click()
        page.locator(".wr-box.done").first.wait_for()
        page.wait_for_function("document.querySelectorAll('.wr-box').length === 2 && document.querySelector('.wr-box.current')", timeout=5000)
        wait_char_ready(page)
        page.get_by_role("button", name="Bỏ qua chữ này").click()
        page.get_by_text("Sai 0 nét · Bỏ qua 2 chữ").wait_for(timeout=5000)
        check("result line after skipping both", page.get_by_text("Sai 0 nét · Bỏ qua 2 chữ").is_visible())
        check("card back shown with Đã thuộc / Chưa thuộc",
              page.locator(".card .hanzi-mid").inner_text() == TARGET["hanzi"]
              and page.get_by_role("button", name="Đã thuộc ✓").is_visible() and page.get_by_role("button", name="Chưa thuộc ✗").is_visible())

        # --- ✍️ Viết sheet from the card back: same card afterwards, progress untouched
        before = progress(page)
        page.get_by_role("button", name="✍️ Viết").click()
        page.locator(".sheet .wr-box").first.wait_for()
        check("sheet opens with the writing UI", page.locator(".sheet .wr-box").count() == 2)
        wait_char_ready(page)
        page.get_by_role("button", name="Đóng").click()
        page.locator(".sheet").wait_for(state="detached")
        check("closing the sheet returns to the same card back",
              page.locator(".card .hanzi-mid").inner_text() == TARGET["hanzi"] and page.get_by_text("1 / 1").is_visible()
              and page.get_by_text("Sai 0 nét · Bỏ qua 2 chữ").is_visible())
        check("progress unchanged by sheet practice", progress(page) == before)
        page.get_by_role("button", name="✍️ Viết").click()
        page.locator(".sheet").wait_for()
        page.go_back()
        page.locator(".sheet").wait_for(state="detached")
        check("browser back closes only the sheet", page.get_by_role("button", name="Đã thuộc ✓").is_visible())

        # --- mark learned in wr; zv/vz stay open for the word
        page.get_by_role("button", name="Đã thuộc ✓").click()
        page.get_by_text("Hoàn thành!").wait_for()
        check("wr learned saved without zv/vz", progress(page).get(TARGET["id"]) == {"zv": 0, "vz": 0, "wr": 1}, str(progress(page).get(TARGET["id"])))
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Luyện viết ✍️").click()
        check("after reload the word does not come back in wr",
              page.get_by_text("Bạn đã thuộc hết HSK 1 (Luyện viết)!").is_visible())
        page.get_by_role("button", name="← Quay lại").click()
        page.get_by_role("button", name="Trung → Việt").first.click()
        check("but it still comes back in Trung → Việt", page.locator(".hanzi-big").inner_text() == TARGET["hanzi"])

        # --- real strokes along the medians. 爱: one wrong line, then every stroke in REVERSED order; 好: normal order.
        seed(page, others={"zv": 1, "vz": 1, "wr": 1})
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Luyện viết ✍️").click()
        wait_char_ready(page)
        box = page.locator(".wr-canvas svg").bounding_box()
        scale = (box["width"] - 2 * PADDING) / 1024
        x = box["x"] + PADDING + 30 * scale
        page.mouse.move(x, box["y"] + box["height"] * 0.25)
        page.mouse.down()
        for t in range(1, 9):
            page.mouse.move(x, box["y"] + box["height"] * (0.25 + 0.05 * t))
        page.mouse.up()
        page.wait_for_timeout(150)
        check("a wrong line does not complete or fill the character", page.locator(".wr-box.done").count() == 0)
        n = len(json.loads((DOCS / "hanzi" / "爱.json").read_text(encoding="utf-8"))["medians"])
        draw_current_char(page, "爱", order=list(reversed(range(n))))
        page.locator(".wr-box.done").first.wait_for(timeout=4000)
        check("strokes drawn in reversed order complete the character", page.locator(".wr-box.done").count() == 1)
        page.wait_for_function("document.querySelector('.wr-box.current') && document.querySelector('.wr-box.current').dataset.i === '1'", timeout=5000)
        wait_char_ready(page)
        draw_current_char(page, "好")
        page.get_by_text("Sai 1 nét · Bỏ qua 0 chữ").wait_for(timeout=6000)
        check("result counts only the wrong line as a mistake", page.get_by_text("Sai 1 nét · Bỏ qua 0 chữ").is_visible())

        # --- a clean run in a shuffled order is "✅ Viết đúng"
        seed(page, others={"zv": 1, "vz": 1, "wr": 1})
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Luyện viết ✍️").click()
        for ch in TARGET["hanzi"]:
            wait_char_ready(page)
            n = len(json.loads((DOCS / "hanzi" / f"{ch}.json").read_text(encoding="utf-8"))["medians"])
            mult = next(m for m in (3, 5, 7, 2) if all(m * i % n != m * j % n for i in range(n) for j in range(i)))
            draw_current_char(page, ch, order=[mult * i % n for i in range(n)])
            page.wait_for_timeout(900)
        page.get_by_text("✅ Viết đúng").wait_for(timeout=6000)
        check("shuffled stroke order -> ✅ Viết đúng", page.get_by_text("✅ Viết đúng").is_visible())

        # --- settings
        page.goto(url + "#")
        page.get_by_role("button", name="Cài đặt").click()
        page.get_by_text("Hiện chữ mờ khi bắt đầu").wait_for()  # Cài đặt draws a moment later (it waits for the saved bank key)
        check("settings has Luyện viết options and the licence line",
              page.get_by_text("Hiện chữ mờ khi bắt đầu").is_visible() and page.get_by_text("Hiện pinyin khi luyện viết").is_visible()
              and page.get_by_text("Hanzi Writer (MIT)").is_visible())
        page.get_by_role("button", name="Tắt").nth(1).click()
        check("pinyin setting saved", page.evaluate("JSON.parse(localStorage.getItem('hskfc.v1.settings')).writingPinyin") is False)
        page.get_by_role("button", name="Bật").nth(1).click()

        # --- offline: characters opened once keep working
        seed(page)
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Luyện viết ✍️").click()
        wait_char_ready(page)
        page.wait_for_timeout(500)
        ctx.set_offline(True)
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Luyện viết ✍️").click()
        page.locator(".wr-boxes").wait_for()
        page.wait_for_timeout(1500)
        check("a character opened before works offline", page.locator(".wr-canvas svg").count() == 1)
        ctx.set_offline(False)

        check("no console/page errors", not errors, "; ".join(errors[:3]))
        browser.close()
    srv.shutdown()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
