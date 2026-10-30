"""Playwright test of Luyện đề (Phase 8) at 390x844, using the made-up fixture bank (never real content).

Usage: python scripts/test_bank.py
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent / "bank"))
import bankcrypto as bc  # noqa: E402

from browser import FIXTURE_BANK, ROOT, launch, serve  # noqa: E402

RESULTS = []
PASSWORD = "test-password"
FIX = json.loads((ROOT / "scripts/fixtures/papers/hsk4-fixture-1/questions.json").read_text(encoding="utf-8"))
QS = {q["id"]: (u, q) for u in FIX["units"] for q in u["questions"]}


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def magic_key():
    meta = json.loads((FIXTURE_BANK / "meta.json").read_text())
    import base64
    key = bc.derive_key(PASSWORD, base64.b64decode(meta["salt"]), meta["iter"])
    return bc.b64url(key)


def bank_progress(page):
    return page.evaluate("JSON.parse(localStorage.getItem('hskfc.v1.bank') || '{}')")


def unlock(page, url, password=PASSWORD):
    page.goto(url)
    page.locator("button.bank-btn").click()
    page.locator("#bank-pw").fill(password)
    page.get_by_role("button", name="Mở khóa").click()


def open_tab(page, tab, size="0"):
    page.locator(f"button[data-action=bank-tab][data-tab={tab}]").click()
    page.locator(f"button[data-action=bank-size][data-value='{size}']").click()


def answer_keys(unit, q, right):
    """Order of tile indices for an ordering question."""
    opts = q["options"]
    if unit["type"] == "order-sentences":
        want = list(q["answer"])
        idx = [next(i for i, o in enumerate(opts) if o["key"] == k) for k in want]
    else:
        text, idx = q["answer"].replace("。", ""), []
        while text:
            i = next(i for i, o in enumerate(opts) if i not in idx and text.startswith(o["text"]))
            idx.append(i)
            text = text[len(opts[i]["text"]):]
    return idx if right else list(reversed(idx))


def answer_question(page, qid, right=True):
    unit, q = QS[qid]
    card = page.locator(f'.qcard[data-qid="{qid}"]')
    if unit["type"] in ("order-words", "order-sentences"):
        for i in answer_keys(unit, q, right):
            card.locator(f'.tiles button.tile[data-i="{i}"]').click()
        card.locator("button[data-action=bank-check]").click()
        return
    if unit["type"] == "tf":
        keys = ["✓", "✗"]
    else:
        keys = [o["key"] for o in (q["options"] or unit["context"]["sharedOptions"])]
    key = q["answer"] if right else next(k for k in keys if k != q["answer"])
    card.locator(f'button.opt[data-key="{key}"]').click()


def play_all(page, wrong_ids=()):
    """Answer every unit of the running set (questions in wrong_ids wrongly). Returns the ids seen."""
    seen = []
    while not page.get_by_text("Hoàn thành!").is_visible():
        ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
        for qid in ids:
            answer_question(page, qid, right=qid not in wrong_ids)
            seen.append(qid)
        page.locator("button[data-action=bank-next]").click()
        assert len(seen) < 60
    return seen


def main():
    errors = []
    with sync_playwright() as p:
        browser = launch(p)

        def new_context(**kw):
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True, **kw)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            return ctx, page

        # ---------- no bank published yet
        srv0, url0 = serve(bank_dir=False)
        ctx, page = new_context()
        page.goto(url0)
        page.locator("button.bank-btn").click()
        page.get_by_text("Chưa có đề — sắp có!").wait_for()
        check("no bank: 'Chưa có đề — sắp có!'", True)
        ctx.close()
        srv0.shutdown()
        errors.clear()  # the single expected 404 for bank/meta.json is not an app error

        srv, url = serve(bank_dir=FIXTURE_BANK)

        # ---------- unlock with the password
        ctx, page = new_context()
        page.goto(url)
        check("Luyện đề button on home", page.locator("button.bank-btn").is_visible())
        page.locator("button.bank-btn").click()
        page.locator("#bank-pw").wait_for()
        page.locator("#bank-pw").fill("sai-mat-khau")
        page.get_by_role("button", name="Mở khóa").click()
        page.get_by_text("Mật khẩu chưa đúng").wait_for()
        check("wrong password message", True)
        page.locator("#bank-pw").fill(PASSWORD)
        page.get_by_role("button", name="Mở khóa").click()
        page.get_by_text("16 câu · Đã làm đúng 0").wait_for()
        check("password unlocks; level list with progress", True)
        check("no readable test text in localStorage/URL", "小猫" not in page.evaluate("JSON.stringify(localStorage)"))

        # ---------- Nghe tab: feedback, progress, wrong -> redo
        page.locator(".level-btn").click()
        page.get_by_text("Còn 5 câu chưa làm đúng").wait_for()
        check("Nghe counts: 5 remaining, 0 wrong", page.get_by_text("Còn 5 câu chưa làm đúng").is_visible() and page.get_by_text("Câu sai: 0").is_visible())
        check("no horizontal scroll at 390px", page.evaluate("document.documentElement.scrollWidth") <= 390)
        open_tab(page, "nghe", "0")
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        check("header 'Câu 1 / 5'-style line", page.locator(".top .title").inner_text().startswith("Câu 1") and page.locator(".top .title").inner_text().endswith("/ 5"))
        check("source label shows the paper title only", page.get_by_text("Nguồn: Đề thử").is_visible())
        check("audio buttons ▶ Nghe and 🔁 Nghe lại", page.get_by_role("button", name="▶ Nghe").first.is_visible() and page.get_by_role("button", name="🔁 Nghe lại").first.is_visible())
        # play a clip
        page.get_by_role("button", name="▶ Nghe").first.click()
        page.wait_for_function("() => { const a = window.__hskBankPlayer; return a.src.startsWith('blob:') && (a.currentTime > 0 || a.ended); }", timeout=5000)
        check("clip decrypted and played", True)
        first_ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
        check("Tiếp disabled until answered", page.locator("button[data-action=bank-next]").is_disabled())
        wrong_id = "hsk4-fixture-1-2"
        # answer the first unit right, to look at the feedback
        unit0, q0 = QS[first_ids[0]]
        answer_question(page, first_ids[0], right=(first_ids[0] != wrong_id))
        check("instant feedback: option marked green (correct) and a result box", page.locator("button.opt.correct").count() >= 1 and page.locator(".fb").first.is_visible())
        check("listening script shown after answering", page.locator(".script, .fb .script").first.is_visible())
        if q0.get("explain_zh"):
            check("Chinese explanation hidden behind a toggle",
                  page.locator("details.expl-zh").count() == 1 and not page.locator("details.expl-zh .zh").is_visible())
            page.locator("details.expl-zh summary").click()
            check("…and opens on tap", page.locator("details.expl-zh .zh").is_visible())
        if q0.get("explain_vi"):
            check("Vietnamese explanation shown", page.locator(".fb .expl").first.is_visible())
        seen = [first_ids[0]]
        for qid in first_ids[1:]:
            answer_question(page, qid, right=(qid != wrong_id))
            seen.append(qid)
        page.locator("button[data-action=bank-next]").click()
        # rest of the set; question 2 wrong when it comes up
        while not page.get_by_text("Hoàn thành!").is_visible():
            ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
            for qid in ids:
                answer_question(page, qid, right=(qid != wrong_id))
                seen.append(qid)
            page.locator("button[data-action=bank-next]").click()
        check("set shows all 5 Nghe questions once", sorted(seen) == sorted(f"hsk4-fixture-1-{n}" for n in range(1, 6)), str(seen))
        check("summary: 4 / 5 correct", page.get_by_text("Đúng 4 / 5 câu").is_visible())
        prog = bank_progress(page)
        check("progress saved: 4 ok, 1 wrong", sum(v["ok"] for v in prog.values()) == 4 and prog[wrong_id] == {"ok": 0, "wrong": 1}, str(prog))
        page.get_by_role("button", name="Về danh sách").click()
        page.get_by_text("Còn 1 câu chưa làm đúng").wait_for()
        check("level screen: 1 remaining, Câu sai: 1", page.get_by_text("Câu sai: 1").is_visible())
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
        check("'Làm câu mới' no longer offers the correct ones", ids == [wrong_id], str(ids))
        page.get_by_label("Quay lại").first.click()
        page.locator("button[data-action=bank-start][data-mode=wrong]").click()
        ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
        check("'Làm lại câu sai' offers the wrong one", ids == [wrong_id], str(ids))
        answer_question(page, wrong_id, right=True)
        page.locator("button[data-action=bank-next]").click()
        page.get_by_text("Hoàn thành!").wait_for()
        page.get_by_role("button", name="Về danh sách").click()
        page.get_by_text("Còn 0 câu chưa làm đúng").wait_for()
        check("wrong answered right: all done in Nghe", page.get_by_text("Câu sai: 0").is_visible() and page.locator("button[data-action=bank-start][data-mode=new]").is_disabled())

        # ---------- reset one tab
        page.locator("button[data-action=bank-reset]").click()
        page.get_by_role("button", name="Xóa và làm lại").click()
        page.get_by_text("Còn 5 câu chưa làm đúng").wait_for()
        check("reset of a tab", bank_progress(page) == {})

        # ---------- Đọc tab: word bank, reading, chips
        open_tab(page, "doc", "0")
        page.locator("button[data-action=bank-chip][data-type=wordbank]").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        check("chip 'Chọn từ' limits the set to the word bank", page.locator(".wordlist").is_visible() and page.locator(".qcard").count() == 3 and page.locator(".top .title").inner_text() == "Câu 1–3 / 3")
        seen = play_all(page)
        check("word bank: 3 blanks answered", len(seen) == 3 and page.get_by_text("Đúng 3 / 3 câu").is_visible())
        page.get_by_role("button", name="Về danh sách").click()
        page.locator("button[data-action=bank-chip][data-type=wordbank]").click()  # chip off again
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        seen = play_all(page, wrong_ids=("hsk4-fixture-1-9",))
        check("reading set: passage + picture units, one wrong", sorted(seen) == [f"hsk4-fixture-1-{n}" for n in (10, 11, 12, 9)] or sorted(seen) == sorted(f"hsk4-fixture-1-{n}" for n in (9, 10, 11, 12)), str(seen))
        page.get_by_role("button", name="Về danh sách").click()
        page.get_by_text("Câu sai: 1").wait_for()
        check("Đọc: wrong one tracked", True)

        # picture options render (decrypted images)
        page.locator("button[data-action=bank-reset]").click()
        page.get_by_role("button", name="Xóa và làm lại").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        found_pics = False
        while not page.get_by_text("Hoàn thành!").is_visible():
            ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
            if page.locator(".opt-grid.pics").count():
                page.wait_for_function("() => [...document.querySelectorAll('img[data-bimg]')].every(i => i.src.startsWith('blob:') && i.naturalWidth > 0)", timeout=5000)
                found_pics = True
            for qid in ids:
                answer_question(page, qid)
            page.locator("button[data-action=bank-next]").click()
        check("picture options decrypted and shown", found_pics)
        page.get_by_role("button", name="Về danh sách").click()

        # ---------- Sắp xếp câu tab
        open_tab(page, "sapxep", "0")
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        # locate each ordering question as it comes; exercise add / remove / clear on the first one
        ids = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
        unit, q = QS[ids[0]]
        card = page.locator(f'.qcard[data-qid="{ids[0]}"]')
        card.locator('.tiles button.tile[data-i="0"]').click()
        card.locator('.tiles button.tile[data-i="1"]').click()
        check("tiles move to the answer line", card.locator(".answer-line button.tile").count() == 2 and card.locator(".tiles button.tile.used").count() == 2)
        card.locator('.answer-line button.tile').first.click()
        check("tapping a tile in the answer line sends it back", card.locator(".answer-line button.tile").count() == 1 and card.locator(".tiles button.tile.used").count() == 1)
        card.locator("button[data-action=bank-clear]").click()
        check("Xóa clears the answer line", card.locator(".answer-line button.tile").count() == 0)
        card.locator("button[data-action=bank-check]").click()
        check("Kiểm tra with unfinished line is refused", page.get_by_text("Hãy xếp đủ các mảnh").is_visible() and bank_progress(page).get(ids[0]) is None)
        answer_question(page, ids[0], right=False)
        check("wrong order: shows ❌ and the correct answer", page.get_by_text("❌ Chưa đúng").is_visible() and page.locator(".right-answer").is_visible())
        if unit["type"] == "order-words" and q.get("alsoAccept"):
            pass
        mine = page.get_by_role("button", name="Câu của mình cũng đúng")
        check("'Câu của mình cũng đúng' offered after a wrong order", mine.is_visible())
        before = bank_progress(page)[ids[0]]
        mine.click()
        after = bank_progress(page)[ids[0]]
        check("…and counts the question as correct", before["ok"] == 0 and after["ok"] == 1 and after["wrong"] == 0, f"{before} -> {after}")
        page.locator("button[data-action=bank-next]").click()
        rest = []
        while not page.get_by_text("Hoàn thành!").is_visible():
            ids2 = page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)")
            for qid in ids2:
                answer_question(page, qid)
                rest.append(qid)
            page.locator("button[data-action=bank-next]").click()
        check("all 4 ordering questions done", len(rest) == 3 and all(v["ok"] for v in bank_progress(page).values() if True) )
        # alternative valid order for 'alsoAccept'
        page.get_by_role("button", name="Về danh sách").click()
        page.locator("button[data-action=bank-reset]").click()
        page.get_by_role("button", name="Xóa và làm lại").click()
        page.locator("button[data-action=bank-chip][data-type=order-words]").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        alt = "hsk4-fixture-1-16"
        done_alt = False
        while not page.get_by_text("Hoàn thành!").is_visible():
            for qid in page.locator(".qcard").evaluate_all("els => els.map(e => e.dataset.qid)"):
                if qid == alt:  # 我们 明天 去公园 (listed in alsoAccept)
                    card = page.locator(f'.qcard[data-qid="{qid}"]')
                    for i in (1, 0, 2):
                        card.locator(f'.tiles button.tile[data-i="{i}"]').click()
                    card.locator("button[data-action=bank-check]").click()
                    done_alt = page.get_by_text("✅ Đúng").first.is_visible()
                else:
                    answer_question(page, qid)
            page.locator("button[data-action=bank-next]").click()
        check("alsoAccept sentence is accepted", done_alt)
        page.get_by_role("button", name="Về danh sách").click()

        # ---------- backup / restore with bank progress
        page.goto(url + "#")
        page.evaluate("localStorage.setItem('hskfc.v1.progress', JSON.stringify({'4-0001': {zv: 1, vz: 0}}))")
        page.reload()
        before = bank_progress(page)
        page.get_by_role("button", name="Cài đặt").click()
        with page.expect_download() as dl:
            page.get_by_role("button", name="Sao lưu tiến độ").click()
        backup = json.loads(Path(dl.value.path()).read_text(encoding="utf-8"))
        check("backup contains word progress and _bank", "4-0001" in backup and backup.get("_bank") == before and len(before) > 0, str(list(backup)[:4]))
        page.evaluate("localStorage.removeItem('hskfc.v1.bank'); localStorage.removeItem('hskfc.v1.progress')")
        page.reload()
        page.get_by_role("button", name="Cài đặt").click()
        page.set_input_files("#restore-file", dl.value.path())
        page.get_by_role("button", name="Khôi phục", exact=True).click()
        page.wait_for_timeout(300)
        check("restore brings the bank progress back", bank_progress(page) == before)
        # an old backup (no _bank) restores words and leaves the bank alone
        old = Path(dl.value.path()).with_name("old-backup.json")
        old.write_text(json.dumps({"4-0001": {"zv": 1, "vz": 0}}))
        page.set_input_files("#restore-file", str(old))
        page.get_by_role("button", name="Khôi phục", exact=True).click()
        page.wait_for_timeout(300)
        check("old backup without _bank still imports", bank_progress(page) == before and page.evaluate("Object.keys(JSON.parse(localStorage.getItem('hskfc.v1.progress'))).length") == 1)

        # ---------- "Tải toàn bộ đề" and "Khóa lại"
        page.get_by_role("button", name="Khóa lại").wait_for()
        # the download button turns into "Đã tải về máy ✓" once every clip is cached (the fixture is tiny and was listened to above)
        has_dl = page.get_by_role("button", name="Tải toàn bộ đề về máy").count() == 1
        check("Cài đặt shows Luyện đề buttons when unlocked", page.get_by_role("button", name="Khóa lại").is_visible() and (has_dl or page.locator("#bank-cached").is_visible()))
        if has_dl:
            page.get_by_role("button", name="Tải toàn bộ đề về máy").click()
            check("download asks first and shows the size", page.get_by_text("MB").first.is_visible())
            page.get_by_role("button", name="Hủy").click()

        # ---------- offline after first use (key in IndexedDB, files in the service-worker cache)
        page.goto(url)
        page.evaluate("navigator.serviceWorker.ready.then(() => true)")
        page.locator("button.bank-btn").click()
        page.get_by_text("16 câu · Đã làm đúng").wait_for()
        page.locator(".level-btn").click()
        open_tab(page, "nghe", "0")
        page.locator("button[data-action=bank-reset]").click()
        page.get_by_role("button", name="Xóa và làm lại").click()
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        page.wait_for_timeout(800)  # clips of the shown unit are fetched and cached
        page.get_by_label("Quay lại").first.click()
        page.get_by_label("Quay lại").first.click()
        # fetch all clips through the download button so every file is cached
        page.goto(url)
        page.get_by_role("button", name="Cài đặt").click()
        page.locator("[data-action=bank-download], #bank-cached").first.wait_for()
        if page.get_by_role("button", name="Tải toàn bộ đề về máy").count():  # else everything is cached already ("Đã tải về máy ✓")
            page.get_by_role("button", name="Tải toàn bộ đề về máy").click()
            page.locator(".dialog button.primary").click()
            page.get_by_text("Đã tải xong").wait_for()
        check("Tải toàn bộ đề về máy completes (or everything was already cached)", True)
        ctx.set_offline(True)
        page.goto(url)
        page.locator("button.bank-btn").click()
        page.get_by_text("16 câu · Đã làm đúng").wait_for()
        check("offline: stays unlocked and the list opens", True)
        page.locator(".level-btn").click()
        open_tab(page, "nghe", "0")
        page.locator("button[data-action=bank-start][data-mode=new]").click()
        page.get_by_role("button", name="▶ Nghe").first.click()
        page.wait_for_function("() => { const a = window.__hskBankPlayer; return a.src.startsWith('blob:') && (a.currentTime > 0 || a.ended); }", timeout=5000)
        check("offline: a cached clip still plays", True)
        ctx.set_offline(False)

        # ---------- Khóa lại
        page.goto(url)
        page.get_by_role("button", name="Cài đặt").click()
        keep = bank_progress(page)
        page.get_by_role("button", name="Khóa lại").click()
        page.get_by_label("Quay lại").first.click()
        page.locator("button.bank-btn").wait_for()
        page.locator("button.bank-btn").click()
        page.locator("#bank-pw").wait_for()
        check("Khóa lại: unlock form again, progress kept", bank_progress(page) == keep)
        page.reload()
        page.locator("button.bank-btn").click()
        page.locator("#bank-pw").wait_for()
        check("Khóa lại survives a reload", True)
        check("no console/page errors (fixture run)", not errors, "; ".join(errors[:3]))
        ctx.close()

        # ---------- magic link
        ctx, page = new_context()
        page.goto(url + "#k=" + magic_key())
        page.get_by_text("16 câu · Đã làm đúng").wait_for()
        check("magic link unlocks", True)
        check("#k= is removed from the address bar", "#k=" not in page.url and "k=" not in page.url, page.url)
        check("…and from history state", "k=" not in json.dumps(page.evaluate("history.state") or {}))
        page.reload()
        page.locator("button.bank-btn").click()
        page.get_by_text("16 câu · Đã làm đúng").wait_for()
        check("magic link key is remembered after reload", True)
        ctx.close()

        # a bad link falls back to the password form
        ctx, page = new_context()
        page.goto(url + "#k=" + "A" * 43)
        page.locator("#bank-pw").wait_for()
        check("wrong magic link -> password form", True)
        ctx.close()

        # ---------- password changed: the saved key no longer matches meta.json
        ctx, page = new_context(service_workers="block")
        unlock(page, url)
        page.get_by_text("16 câu · Đã làm đúng").wait_for()
        meta = json.loads((FIXTURE_BANK / "meta.json").read_text())
        meta["salt"] = bc.b64(b"another-salt-123"); meta["check"] = bc.b64(bc.encrypt(b"k" * 32, bc.CHECK_PLAINTEXT))
        page.route("**/bank/meta.json", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(meta)))
        page.goto(url)
        page.locator("button.bank-btn").click()
        page.get_by_text("Mật khẩu đã đổi, vui lòng nhập lại.").wait_for()
        check("changed password: asks again with a clear message", True)
        ctx.close()

        browser.close()
    srv.shutdown()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
