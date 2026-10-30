"""Playwright test of Trắc nghiệm (Phase 9 part B) at 390x844, with the real public word data. No bank involved.

Usage: python scripts/test_quiz.py
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser import ROOT, launch, serve  # noqa: E402

RESULTS = []
HSK1 = {w["id"]: w for w in json.loads((ROOT / "docs/data/hsk1.json").read_text(encoding="utf-8"))["words"]}

VOICE_JS = """
(() => {
  const voices = %s;
  window.__spoken = [];
  const synth = { getVoices: () => voices, speak: (u) => { window.__spoken.push(u.text); }, cancel() {}, addEventListener() {}, onvoiceschanged: null };
  Object.defineProperty(window, 'speechSynthesis', { value: synth, configurable: true });
  window.SpeechSynthesisUtterance = function (t) { this.text = t; };
})();
"""
WITH_VOICE = VOICE_JS % '[{lang: "zh-CN", name: "Mock", voiceURI: "mock", default: true, localService: true}]'
NO_VOICE = VOICE_JS % "[]"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def storage(page, key):
    return page.evaluate(f"JSON.parse(localStorage.getItem('{key}') || '{{}}')")


def set_storage(page, key, value):
    page.evaluate("([k, v]) => localStorage.setItem(k, JSON.stringify(v))", [key, value])


def open_quiz(page, url, level=1):
    page.goto(url)
    page.locator(f".level-btn[data-level='{level}']").click()
    page.get_by_role("button", name="Trắc nghiệm").click()
    page.get_by_text("Loại câu").wait_for()


def start(page, mode="new"):
    page.locator(f"button[data-action=quiz-start][data-mode={mode}]").click()
    page.locator(".qcard").wait_for()


def pick(page, right=True):
    ans = page.locator(".qcard").get_attribute("data-answer")
    key = ans if right else next(k for k in "ABCD" if k != ans)
    page.locator(f"button[data-action=quiz-pick][data-key={key}]").click()
    page.locator(".quiz-fb").wait_for()
    return page.locator(".qcard").get_attribute("data-wid")


def nxt(page):
    page.locator("button[data-action=quiz-next]").click()


def chip(page, type_id):
    return page.locator(f"button[data-action=quiz-chip][data-type={type_id}]")


def main():
    srv, url = serve(False)
    with sync_playwright() as p:
        browser = launch(p)

        def new_page(voice=WITH_VOICE):
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
            ctx.add_init_script(voice)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "favicon" not in m.text else None)
            return ctx, page, errors

        ctx, page, errors = new_page()

        # ---------- level screen -> setup
        page.goto(url)
        page.locator(".level-btn[data-level='1']").click()
        btn = page.get_by_role("button", name="Trắc nghiệm")
        btn.wait_for()
        page.get_by_text("Còn 500 từ chưa làm đúng").wait_for()
        check("level screen has the Trắc nghiệm button with the remaining count", btn.is_visible() and "Còn 500 từ chưa làm đúng" in btn.inner_text(), btn.inner_text())
        labels = [b.inner_text().strip() for b in page.locator("button.btn.primary, button.btn").all()]
        i_wr = next(i for i, t in enumerate(labels) if t.startswith("Luyện viết")); i_q = next(i for i, t in enumerate(labels) if t.startswith("Trắc nghiệm")); i_rv = next(i for i, t in enumerate(labels) if t.startswith("Ôn lại"))
        check("button sits after Luyện viết and before Ôn lại", i_wr < i_q < i_rv, str(labels))
        btn.click()
        page.get_by_text("Loại câu").wait_for()
        check("setup: six type chips, all on", page.locator("button[data-action=quiz-chip]").count() == 6 and page.locator("button[data-action=quiz-chip][aria-pressed=true]").count() == 6)
        check("setup: defaults are Tất cả từ and 20", page.locator("button[data-action=quiz-pool][data-value=all]").get_attribute("aria-pressed") == "true" and page.locator("button[data-action=quiz-size][data-value='20']").get_attribute("aria-pressed") == "true")
        check("setup: new / wrong / reset / back buttons", page.locator("button[data-action=quiz-start][data-mode=new]").is_enabled() and page.locator("button[data-action=quiz-start][data-mode=wrong]").is_disabled()
              and page.locator("button[data-action=quiz-reset]").is_visible() and page.get_by_role("button", name="← Quay lại").is_visible())
        check("setup: Làm câu mới shows the word count", "từ" in page.locator("button[data-action=quiz-start][data-mode=new]").inner_text())

        # ---------- chips: toggle, remembered, at least one stays on
        chip(page, "hanviet").click()
        check("chip toggled off and remembered", "hanviet" not in storage(page, "hskfc.v1.settings")["quizTypes"] and chip(page, "hanviet").get_attribute("aria-pressed") == "false")
        for t in ["nghia", "chuhan", "pinyin", "nghe"]:
            chip(page, t).click()
        chip(page, "dientu").click()  # the last one: refused
        check("at least one type must stay on", storage(page, "hskfc.v1.settings")["quizTypes"] == ["dientu"] and chip(page, "dientu").get_attribute("aria-pressed") == "true")
        page.reload()  # the app starts at home again: the choice must have been remembered
        open_quiz(page, url)
        check("the chosen types are remembered after a reload", storage(page, "hskfc.v1.settings")["quizTypes"] == ["dientu"] and chip(page, "dientu").get_attribute("aria-pressed") == "true")
        for t in ["nghia", "chuhan", "pinyin", "nghe", "hanviet"]:
            chip(page, t).click()
        check("all six types back on", storage(page, "hskfc.v1.settings")["quizTypes"] == ["nghia", "chuhan", "pinyin", "nghe", "dientu", "hanviet"])
        page.locator("button[data-action=quiz-size][data-value='10']").click()
        check("set size saved", storage(page, "hskfc.v1.settings")["quizSize"] == 10)

        # ---------- a set of 10 with all types: header, prompt per type, options, card after answering
        start(page)
        check("header shows HSK 1 · Trắc nghiệm and Câu 1 / 10", page.get_by_text("HSK 1 · Trắc nghiệm").is_visible() and page.get_by_text("Câu 1 / 10").is_visible())
        seen_types = set()
        wrongs = []
        rights = []
        for n in range(10):
            qtype = page.locator(".qcard").get_attribute("data-type")
            seen_types.add(qtype)
            check_opts = page.locator("button[data-action=quiz-pick]")
            if n == 0:
                texts = [check_opts.nth(i).inner_text() for i in range(4)]
                check("four options A–D, all different", check_opts.count() == 4 and len(set(texts)) == 4 and [check_opts.nth(i).locator(".k").inner_text() for i in range(4)] == list("ABCD"), str(texts))
                check("no card before answering", page.locator(".quiz-card").count() == 0 and page.locator("button[data-action=quiz-next]").is_disabled())
            right = n % 3 != 0  # words 0, 3, 6, 9 are answered wrong
            wid = pick(page, right)
            (rights if right else wrongs).append(wid)
            if n == 0:
                check("wrong option red, right option green", page.locator(".opt.wrong").count() == 1 and page.locator(".opt.correct").count() == 1)
                check("card shows after answering (hanzi, pinyin, nghĩa, example)", page.locator(".quiz-card .hanzi-mid").is_visible() and page.locator(".quiz-card .pinyin").is_visible()
                      and page.locator(".quiz-card .meaning").is_visible() and page.locator(".quiz-card .example .zh").is_visible())
                check("a wrong answer for a not-learned word has no 'Thêm vào ôn tập'", page.get_by_role("button", name="Thêm vào ôn tập").count() == 0)
            nxt(page) if n < 9 else page.locator("button[data-action=quiz-next]").click()
        page.get_by_text("Hoàn thành!").wait_for()
        check("summary shows correct / total and the wrong words", f"{len(rights)} / 10" in page.locator(".screen").inner_text() and page.locator(".wrong-list .wrow").count() == len(wrongs))
        q = storage(page, "hskfc.v1.quiz")
        check("progress saved per word: right ok=1, wrong ok=0 wrong=1", all(q[w]["ok"] == 1 for w in rights) and all(q[w] == {"ok": 0, "wrong": 1} for w in wrongs), str(q))
        check("flashcard progress untouched", storage(page, "hskfc.v1.progress") == {})
        page.get_by_role("button", name="Về cấp độ").click()
        page.get_by_role("button", name="Trắc nghiệm").wait_for()
        check("level screen count went down by the correct words", f"Còn {500 - len(rights)} từ chưa làm đúng" in page.get_by_role("button", name="Trắc nghiệm").inner_text())

        # ---------- Làm câu mới leaves correct words out; Làm lại câu sai offers the wrong ones
        page.get_by_role("button", name="Trắc nghiệm").click()
        check("setup counts: remaining and wrong", f"Còn {500 - len(rights)} từ chưa làm đúng" in page.locator(".bank-stats").inner_text() and f"Từ sai: {len(wrongs)}" in page.locator(".bank-stats").inner_text())
        check("Làm lại câu sai shows its count", f"{len(wrongs)} từ" in page.locator("button[data-action=quiz-start][data-mode=wrong]").inner_text())
        page.locator("button[data-action=quiz-size][data-value='0']").click()
        start(page, "wrong")
        seen = []
        for _ in range(len(wrongs)):
            seen.append(page.locator(".qcard").get_attribute("data-wid"))
            pick(page, True)
            nxt(page) if _ < len(wrongs) - 1 else page.locator("button[data-action=quiz-next]").click()
        check("Làm lại câu sai asks exactly the wrong words", sorted(seen) == sorted(wrongs), f"{seen} vs {wrongs}")
        page.get_by_text("Hoàn thành!").wait_for()
        q = storage(page, "hskfc.v1.quiz")
        check("a wrong word answered right becomes ok=1 and keeps its wrong count", all(q[w] == {"ok": 1, "wrong": 1} for w in wrongs))
        page.get_by_role("button", name="Về cấp độ").click()
        page.get_by_role("button", name="Trắc nghiệm").click()
        page.locator("button[data-action=quiz-size][data-value='10']").click()
        check("no wrong words left: the button is disabled", page.locator("button[data-action=quiz-start][data-mode=wrong]").is_disabled())
        start(page)
        asked = page.locator(".qcard").get_attribute("data-wid")
        check("Làm câu mới never asks an already-correct word", asked not in rights + wrongs)

        # ---------- reset
        page.get_by_label("Quay lại").first.click()
        page.locator("button[data-action=quiz-reset]").click()
        page.get_by_role("button", name="Xóa và làm lại").click()
        check("reset clears the level's quiz progress", storage(page, "hskfc.v1.quiz") == {})

        # ---------- Chỉ từ đã thuộc
        page.locator("button[data-action=quiz-pool][data-value=learned]").click()
        check("learned pool with nothing learned: friendly line, start buttons disabled", page.locator("#quiz-none-learned").is_visible() and page.locator("button[data-action=quiz-start][data-mode=new]").is_disabled())
        set_storage(page, "hskfc.v1.progress", {"1-0001": {"zv": 1, "vz": 0}, "1-0002": {"zv": 0, "vz": 1}, "1-0003": {"zv": 0, "vz": 0, "wr": 1}})
        page.reload()
        open_quiz(page, url)
        check("learned pool counts words learned in any direction (zv, vz, wr)", "3 từ" in page.locator("button[data-action=quiz-start][data-mode=new]").inner_text(), page.locator("button[data-action=quiz-start][data-mode=new]").inner_text())
        page.locator("button[data-action=quiz-size][data-value='0']").click()
        start(page)
        ids = []
        for i in range(3):
            ids.append(page.locator(".qcard").get_attribute("data-wid"))
            pick(page, True)
            nxt(page) if i < 2 else page.locator("button[data-action=quiz-next]").click()
        check("only learned words were asked", sorted(ids) == ["1-0001", "1-0002", "1-0003"], str(ids))
        page.get_by_text("Hoàn thành!").wait_for()
        page.get_by_role("button", name="Về cấp độ").click()

        # ---------- Thêm vào ôn tập: a learned word answered wrong goes back to the flash cards
        set_storage(page, "hskfc.v1.progress", {"1-0001": {"zv": 1, "vz": 1}})
        set_storage(page, "hskfc.v1.quiz", {})
        page.reload()
        open_quiz(page, url)
        page.locator("button[data-action=quiz-pool][data-value=learned]").click()
        start(page)
        pick(page, False)
        add = page.get_by_role("button", name="Thêm vào ôn tập")
        check("wrong + learned word: 'Thêm vào ôn tập' is offered", add.is_visible())
        add.click()
        page.get_by_text("Đã thêm vào ôn tập").wait_for()
        check("the word is back in flash-card study (zv and vz cleared)", "1-0001" not in storage(page, "hskfc.v1.progress"), str(storage(page, "hskfc.v1.progress")))
        check("the button is gone after use", page.get_by_role("button", name="Thêm vào ôn tập").count() == 0)
        page.locator("button[data-action=quiz-next]").click()
        page.get_by_text("Hoàn thành!").wait_for()
        page.get_by_role("button", name="Về cấp độ").click()
        check("flash-card level screen counts it again", "Còn 500 từ" in page.locator("button[data-action=study][data-dir=zv]").inner_text())
        # a right answer never offers it
        set_storage(page, "hskfc.v1.progress", {"1-0001": {"zv": 1, "vz": 0}})
        page.reload()
        open_quiz(page, url)
        page.locator("button[data-action=quiz-pool][data-value=learned]").click()
        start(page)
        pick(page, True)
        check("right answer: no 'Thêm vào ôn tập'", page.get_by_role("button", name="Thêm vào ôn tập").count() == 0)

        # ---------- every type shows up, with the right prompt
        set_storage(page, "hskfc.v1.progress", {})
        set_storage(page, "hskfc.v1.quiz", {})
        page.reload()
        open_quiz(page, url)
        page.locator("button[data-action=quiz-pool][data-value=all]").click()
        page.locator("button[data-action=quiz-size][data-value='50']").click()
        start(page)
        types = {}
        for n in range(50):
            t = page.locator(".qcard").get_attribute("data-type")
            if t not in types:
                types[t] = page.locator(".qcard").inner_text()
            pick(page, True)
            nxt(page) if n < 49 else page.locator("button[data-action=quiz-next]").click()
        check("all six types appear in a set of 50", set(types) == {"nghia", "chuhan", "pinyin", "nghe", "dientu", "hanviet"}, str(sorted(types)))
        check("dientu shows a blank ＿＿ and a Gợi ý button", "＿＿" in types.get("dientu", "") and "Gợi ý" in types.get("dientu", ""))
        check("nghe shows only a listen button, no text", "🔊 Nghe" in types.get("nghe", ""))
        page.get_by_text("Hoàn thành!").wait_for()
        page.get_by_role("button", name="Về cấp độ").click()

        # ---------- listening type: tap plays the word, Tiếp plays the next one by itself
        page.get_by_role("button", name="Trắc nghiệm").click()
        for t in ["nghia", "chuhan", "pinyin", "dientu", "hanviet"]:
            chip(page, t).click()
        page.locator("button[data-action=quiz-size][data-value='10']").click()
        page.evaluate("window.__spoken.length = 0")
        start(page)
        check("nghe question: nothing plays before the first tap", page.evaluate("window.__spoken.length") == 0)
        page.get_by_role("button", name="🔊 Nghe").click()
        w1 = HSK1[page.locator(".qcard").get_attribute("data-wid")]["hanzi"]
        check("tap on 🔊 Nghe speaks the hanzi", page.evaluate("window.__spoken.at(-1)") == w1, str(page.evaluate("window.__spoken")))
        pick(page, True)
        nxt(page)
        w2 = HSK1[page.locator(".qcard").get_attribute("data-wid")]["hanzi"]
        check("Tiếp plays the next listening question automatically", page.evaluate("window.__spoken.at(-1)") == w2 and page.evaluate("window.__spoken.length") == 2)
        page.get_by_role("button", name="🔁 Nghe lại").click()
        check("🔁 Nghe lại speaks it again", page.evaluate("window.__spoken.length") == 3)

        # ---------- dientu hint
        page.get_by_label("Quay lại").first.click()
        page.get_by_text("Loại câu").wait_for()
        chip(page, "dientu").click()  # dientu on ...
        chip(page, "nghe").click()    # ... nghe off: only fill-in-the-blank questions
        check("only dientu is on", storage(page, "hskfc.v1.settings")["quizTypes"] == ["dientu"])
        start(page)
        check("dientu question starts without the translation", page.locator("#quiz-hint-text").count() == 0)
        page.get_by_role("button", name="Gợi ý").click()
        check("Gợi ý reveals the Vietnamese translation", page.locator("#quiz-hint-text").inner_text().strip() != "")
        check("no page errors so far", not errors, str(errors))
        ctx.close()

        # ---------- no Chinese voice: nghe is hidden with a note
        ctx2, page2, errors2 = new_page(NO_VOICE)
        open_quiz(page2, url)
        check("no voice: the listening chip is hidden", chip(page2, "nghe").count() == 0 and page2.locator("button[data-action=quiz-chip]").count() == 5)
        check("no voice: one-line note with the hint", page2.get_by_text("Máy chưa có giọng đọc tiếng Trung").is_visible())
        page2.locator("button[data-action=quiz-size][data-value='50']").click()
        start(page2)
        kinds = set()
        for n in range(50):
            kinds.add(page2.locator(".qcard").get_attribute("data-type"))
            pick(page2, True)
            nxt(page2) if n < 49 else page2.locator("button[data-action=quiz-next]").click()
        check("no voice: no listening question is ever asked", "nghe" not in kinds and len(kinds) >= 4, str(kinds))
        ctx2.close()

        # ---------- backup / restore carries _quiz
        ctx3, page3, errors3 = new_page()
        page3.goto(url)
        set_storage(page3, "hskfc.v1.quiz", {"1-0001": {"ok": 1, "wrong": 0}, "1-0002": {"ok": 0, "wrong": 2}})
        page3.reload()
        page3.get_by_role("button", name="Cài đặt").click()
        with page3.expect_download() as dl:
            page3.get_by_role("button", name="Sao lưu tiến độ").click()
        backup = json.loads(Path(dl.value.path()).read_text(encoding="utf-8"))
        check("backup contains _quiz", backup.get("_quiz") == {"1-0001": {"ok": 1, "wrong": 0}, "1-0002": {"ok": 0, "wrong": 2}})
        page3.evaluate("localStorage.removeItem('hskfc.v1.quiz')")
        page3.reload()
        page3.get_by_role("button", name="Cài đặt").click()
        page3.set_input_files("#restore-file", dl.value.path())
        page3.get_by_role("button", name="Khôi phục", exact=True).click()
        page3.wait_for_timeout(300)
        check("restore brings the quiz progress back", storage(page3, "hskfc.v1.quiz") == backup["_quiz"])
        old = Path(dl.value.path()).with_name("old-backup-quiz.json")
        old.write_text(json.dumps({"1-0001": {"zv": 1, "vz": 0}}))
        page3.set_input_files("#restore-file", str(old))
        page3.get_by_role("button", name="Khôi phục", exact=True).click()
        page3.wait_for_timeout(300)
        check("an old backup (no _quiz) leaves the quiz progress alone", storage(page3, "hskfc.v1.quiz") == backup["_quiz"])

        # ---------- offline after the first load
        page3.goto(url)
        page3.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page3.reload()
        page3.locator(".level-btn[data-level='2']").click()
        page3.get_by_role("button", name="Trắc nghiệm").click()
        page3.get_by_text("Loại câu").wait_for()
        page3.wait_for_timeout(500)
        ctx3.set_offline(True)
        page3.goto(url)
        page3.locator(".level-btn[data-level='2']").click()
        page3.get_by_role("button", name="Trắc nghiệm").click()
        page3.get_by_text("Loại câu").wait_for()
        start(page3)
        pick(page3, True)
        check("offline: the quiz of a level opened before still works", page3.locator(".quiz-card").is_visible())
        check("no page errors (backup/offline part)", not errors3, str(errors3))
        ctx3.close()
        browser.close()
    srv.shutdown()
    bad = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} passed")
    sys.exit(1 if bad else 0)


main()
