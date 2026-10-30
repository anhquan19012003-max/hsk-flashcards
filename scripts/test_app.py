"""End-to-end test of docs/ in a 390x844 browser. Serves docs/ itself on a free port.

Usage: python scripts/test_app.py
"""
import functools
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WORDS = json.loads((DOCS / "data" / "hsk1.json").read_text(encoding="utf-8"))["words"]
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


def progress(page):
    return page.evaluate("JSON.parse(localStorage.getItem('hskfc.v1.progress') || '{}')")


def learned(page, dir_):
    return sum(1 for v in progress(page).values() if v.get(dir_))


def study_session(page, dir_, answer_all=True):
    """Press 'Đã thuộc' on every card until the summary appears. Returns number of cards seen."""
    seen = 0
    while not page.locator("text=Hoàn thành!").is_visible():
        page.locator("button[data-action=flip]").click()
        page.get_by_role("button", name="Đã thuộc ✓").click()
        seen += 1
        assert seen < 200
    return seen


def main():
    srv, url = serve()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(url)

        # --- home / level
        expect(page.get_by_text("HSK 1", exact=True)).to_be_visible()
        check("home shows 5 levels", page.locator(".level-btn").count() == 5)
        page.locator(".level-btn").first.click()
        page.get_by_text("Còn 500 từ").first.wait_for()
        check("level screen remaining 500", page.get_by_text("Còn 500 từ").count() == 2)

        # --- Trung → Việt: one session of 20 (default size)
        page.get_by_role("button", name="Trung → Việt").first.click()
        check("header shows 1 / 20", page.get_by_text("1 / 20").is_visible())
        front = page.locator(".hanzi-big").inner_text()
        check("front shows hanzi big", len(front) >= 1 and page.locator(".hanzi-big").evaluate("e => parseFloat(getComputedStyle(e).fontSize)") >= 64)
        page.locator("button[data-action=flip]").click()
        check("back shows pinyin + meaning", page.locator(".pinyin").is_visible() and page.locator(".meaning").is_visible())
        page.get_by_role("button", name="Đã thuộc ✓").click()
        check("header advances to 2 / 20", page.get_by_text("2 / 20").is_visible())

        # --- Chưa thuộc: card returns 5-8 cards later
        page.locator("button[data-action=flip]").click()
        target = page.locator(".card .hanzi-mid").inner_text()
        target_meaning = page.locator(".meaning").inner_text()
        page.get_by_role("button", name="Chưa thuộc ✗").click()
        gap = None
        for i in range(1, 12):
            page.locator("button[data-action=flip]").click()
            if page.locator(".meaning").inner_text() == target_meaning and page.locator(".card .hanzi-mid").inner_text() == target:
                gap = i
                break
            page.get_by_role("button", name="Đã thuộc ✓").click()
        check("'Chưa thuộc' card returns 5-8 cards later", gap is not None and 5 <= gap <= 8, f"gap={gap}")
        page.get_by_role("button", name="Đã thuộc ✓").click()
        study_session(page, "zv")
        check("summary shows Hoàn thành", page.locator("text=Hoàn thành!").is_visible())
        check("19 distinct+1 learned = 20 in zv", learned(page, "zv") == 20, str(learned(page, "zv")))
        check("summary lists retry count", page.locator(".stat.bad b").inner_text() == "1")

        # --- reload: learned words must not come back
        page.reload()
        check("home shows Đã thuộc 20 after reload", page.get_by_text("500 từ · Đã thuộc 20").is_visible())
        first_before = set(k for k, v in progress(page).items() if v["zv"])
        page.locator(".level-btn").first.click()
        page.get_by_text("Còn 480 từ").first.wait_for()
        check("remaining 480 after reload", page.get_by_text("Còn 480 từ").count() >= 1)
        page.get_by_role("button", name="Trung → Việt").first.click()
        study_session(page, "zv")
        check("second session adds 20 new (no repeats of learned)", learned(page, "zv") == 40, str(learned(page, "zv")))
        check("earlier ids still learned", first_before <= set(k for k, v in progress(page).items() if v["zv"]))
        page.get_by_role("button", name="Về trang chủ").click()

        # --- Việt → Trung with answer checking
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Việt → Trung (gõ đáp án)").click()
        check("answer input has phone attrs", page.locator("#answer").evaluate(
            "e => e.getAttribute('autocapitalize') === 'off' && e.getAttribute('autocorrect') === 'off' && e.getAttribute('spellcheck') === 'false'"))
        meanings = {}
        for w in WORDS:
            meanings.setdefault(w["meaning"], []).append(w)
        tested = {"right": 0, "wrong": 0}
        for step in range(20):
            meaning = page.locator(".meaning-big").inner_text()
            cands = meanings[meaning]
            if step == 0:  # wrong answer first
                page.fill("#answer", "zzzz")
                page.get_by_role("button", name="Kiểm tra").click()
                if page.get_by_text("❌ Chưa đúng").is_visible() and page.get_by_text("Bạn gõ: zzzz").is_visible():
                    tested["wrong"] += 1
            else:
                w = cands[0]
                variants = [w["hanzi"], w["pinyin"], "".join(c for c in w["pinyin"].lower())]
                typed = [w["hanzi"], w["pinyin"].upper(), " ".join(w["pinyin"])][step % 3]
                page.fill("#answer", typed)
                page.get_by_role("button", name="Kiểm tra").click()
                if page.get_by_text("✅ Đúng").is_visible():
                    tested["right"] += 1
            page.get_by_role("button", name="Đã thuộc ✓").click()
            if page.locator("text=Hoàn thành!").is_visible():
                break
        check("wrong answer shows ❌ with typed text", tested["wrong"] == 1)
        check("correct answers (hanzi / PINYIN / spaced pinyin) accepted", tested["right"] >= 17, str(tested))
        study_session(page, "vz")
        check("vz learned counted separately", learned(page, "vz") == 20, str(learned(page, "vz")))
        page.get_by_role("button", name="Về trang chủ").click()

        # --- review mode
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Ôn lại từ đã thuộc").click()
        page.get_by_role("button", name="Trung → Việt (40 từ)").click()
        check("review header 1 / 20", page.get_by_text("1 / 20").is_visible())
        page.locator("button[data-action=flip]").click()
        check("review buttons", page.get_by_role("button", name="Vẫn nhớ ✓").is_visible() and page.get_by_role("button", name="Quên rồi ✗").is_visible())
        page.get_by_role("button", name="Quên rồi ✗").click()
        page.locator("button[data-action=flip]").click()
        page.get_by_role("button", name="Vẫn nhớ ✓").click()
        check("'Quên rồi' un-learns the word", learned(page, "zv") == 39, str(learned(page, "zv")))
        page.get_by_label("Quay lại").first.click()
        check("back arrow leaves session", page.get_by_text("Học lại từ đầu").is_visible())

        # --- backup / restore
        page.goto(url + "#")
        page.get_by_role("button", name="Cài đặt").click()
        with page.expect_download() as dl:
            page.get_by_role("button", name="Sao lưu tiến độ").click()
        path = dl.value.path()
        backup = json.loads(Path(path).read_text(encoding="utf-8"))
        check("backup has progress shape", len(backup) >= 40 and set(next(iter(backup.values()))) == {"zv", "vz"})
        page.get_by_role("button", name="20", exact=True).click()
        page.get_by_role("button", name="10", exact=True).click()
        check("session size setting saved", page.evaluate("JSON.parse(localStorage.getItem('hskfc.v1.settings')).sessionSize") == 10)
        page.evaluate("localStorage.removeItem('hskfc.v1.progress')")
        page.reload()
        page.get_by_role("button", name="Cài đặt").click()
        page.set_input_files("#restore-file", str(path))
        page.get_by_role("button", name="Khôi phục", exact=True).click()
        check("restore brings progress back", len(progress(page)) == len(backup), f"{len(progress(page))} vs {len(backup)}")

        # --- reset level
        page.get_by_label("Quay lại").first.click()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Học lại từ đầu").click()
        page.get_by_role("button", name="Xóa và học lại").click()
        check("reset clears level", len(progress(page)) == 0)

        # --- all learned screen
        page.evaluate("""() => {
          const p = {}; for (let i = 1; i <= 500; i++) p['1-' + String(i).padStart(4, '0')] = {zv: 1, vz: 0};
          localStorage.setItem('hskfc.v1.progress', JSON.stringify(p)); }""")
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_role("button", name="Trung → Việt").first.click()
        check("all-learned message", page.get_by_text("Bạn đã thuộc hết HSK 1 (chiều Trung → Việt)!").is_visible())

        # --- offline
        page.evaluate("localStorage.clear()")
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page.locator(".level-btn").first.click()  # loads hsk1.json into the data cache
        page.wait_for_timeout(500)
        ctx.set_offline(True)
        page.reload()
        page.locator(".level-btn").first.click()
        page.get_by_text("Còn 500 từ").first.wait_for()
        check("works offline (shell + level data cached)", page.get_by_text("Còn 500 từ").count() == 2)
        ctx.set_offline(False)

        check("no console/page errors", not errors, "; ".join(errors[:3]))
        browser.close()
    srv.shutdown()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
