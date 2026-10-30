# Phase 7 — Luyện viết (writing practice)

Let learners write each character of a word with their finger on the phone. The app checks every stroke's shape and direction (any order — see the 2026-10-30 change below), gives hints, and can animate the correct stroke order. No paid API, no server, and it keeps working offline.

Quan's decisions (2026-10-30):
- Writing practice appears in **two places**: its own mode on the level screen, and a button on the back of every card.
- It uses the same "random, skip learned" logic as the other modes, with its own learned status.

Read the whole spec before starting. Check the Hanzi Writer docs (https://hanziwriter.org/docs.html) for exact option and method names rather than relying on memory.

---

## 1. Library and data

**Hanzi Writer** (npm `hanzi-writer`, MIT licence) does the drawing, stroke checking and animation.
- Vendor the minified build into `docs/vendor/hanzi-writer.min.js` and pin the version (note it in `PROGRESS.md`). **No CDN at runtime** — the app must work offline and keep working if a CDN changes.

**Character data** (npm `hanzi-writer-data`, derived from Make Me a Hanzi; Arphic Public License).
- Write `scripts/build_hanzi_data.py` (or a small Node script). It collects every distinct Han character in `docs/data/hsk1..5.json` (currently **1,590 characters**) and copies only those files to `docs/hanzi/{char}.json`.
- Report the total size and any characters with no data.
- It must be re-runnable: call it from `scripts/build.py` so it stays in sync when the vocabulary changes.
- Load characters with Hanzi Writer's `charDataLoader`, fetching `hanzi/` + `encodeURIComponent(char)` + `.json`.

**Licences**
- Copy Hanzi Writer's `LICENSE` and the data's `ARPHICPL.TXT` into `docs/vendor/`.
- In Cài đặt add a small "Nguồn & giấy phép" line: "Luyện viết dùng Hanzi Writer (MIT) và dữ liệu nét chữ từ Make Me a Hanzi / Arphic (Arphic Public License)."

**Service worker (`docs/sw.js`)**
- Add `vendor/hanzi-writer.min.js` and any new JS module to `SHELL`.
- Add a separate cache `hskfc-hanzi` for `/hanzi/*.json`: cache-first, stored on first use. **Do not precache all 1,590 files.** Keep this cache across versions, like `hskfc-data`.
- Bump `VERSION` (`scripts/bump_version.py`).

---

## 2. Where it appears

**A. Level screen** — new button between "Việt → Trung" and "Ôn lại":
`Luyện viết ✍️` with `Còn N từ` underneath.
The "Ôn lại từ đã thuộc" picker gets a third choice, `Luyện viết`, and its counts line shows all three directions.

**B. Back of every card** (all modes) — a small `✍️ Viết` button next to the word's 🔊.
- It opens the writing panel for that word as a full-screen sheet.
- `Đóng` returns to the **same card with the same state**: the session doesn't move and the result isn't lost.
- Practising from here **does not change progress**.

---

## 3. Writing session (direction key `wr`)

Same mechanics as the existing modes:
- random shuffle of words not learned in `wr`
- session size from settings
- `Chưa thuộc` puts the card back 5–8 cards later
- end-of-session summary
- review mode with `Vẫn nhớ` / `Quên rồi`
- the "all learned" screen

Reuse the existing session code; add `wr` as a third `dir`.

**Front (the prompt):** Vietnamese meaning, từ loại, pinyin, and 🔊 for the word. Pinyin is shown by default because the skill being tested is writing, not recall from meaning; a setting can hide it (see §5). Below the prompt, a row of small boxes, one per character, so the learner sees how many characters to write and which one they're on.

**Writing area:** one character at a time, in order.
- Square, `min(80vw, 300px)`, with a 米字格 practice grid behind it (thin dashed diagonal and centre lines, drawn as SVG or CSS — not part of the quiz).
- Quiz (changed 2026-10-30 — strokes may be written in ANY order; Hanzi Writer's own quiz is strict about order, so grading is custom in `docs/js/strokematch.js`; Hanzi Writer still draws the outline and the animation):
  - the character itself is hidden
  - the outline is hidden by default (toggle below)
  - each drawn line is matched against every stroke not yet written (shape + direction, tolerance ~10% of the box); a match paints that stroke, no match = 1 mistake
  - hint (one missing stroke flashes) after 3 wrong lines in a row
  - strokes turn green on complete
- When a character is finished, fill its small box at the top with the character, pause about 0.5 s, then move to the next.

**Buttons under the writing area:**
| Button | Does |
|---|---|
| `Xem cách viết` | Animate the current character's stroke order, then restart the quiz for it |
| `Hiện chữ mờ` / `Ẩn chữ mờ` | Toggle the faint outline (tracing aid); remember the choice in settings |
| `Viết lại` | Restart the current character |
| `Bỏ qua chữ này` | Mark the character skipped, show it, move on |

**Special characters**
- Non-Han characters (the brackets in `有(一)些`, `有(一)点儿`) are shown as static text, not quizzed.
- Repeated characters (e.g. 爸爸) are quizzed each time.
- A character with no data file is shown statically with a small note: "Chưa có dữ liệu nét cho chữ này."

**After the last character:**
- Show a result line:
  - `✅ Viết đúng` when there were no mistakes and no skips
  - otherwise `Sai X nét · Bỏ qua Y chữ`
- Then show the normal card back (pinyin, Hán Việt, meaning, example + 🔊).
- Then the usual `Đã thuộc ✓` / `Chưa thuộc ✗` buttons — the learner decides, as in the other modes.

---

## 4. Phone experience (important — this is where it can go wrong)

- Drawing must never scroll the page. Use `touch-action: none` on the writing area, and `overscroll-behavior: contain` on the page while the writing screen is open, so pull-to-refresh and swipes don't fire mid-stroke.
- Keep about 16 px margin from screen edges so iOS edge-swipe-back doesn't fire.
- No toasts or dialogs over the writing area while a quiz is running.
- Large enough buttons (≥ 44 px); the writing area stays fully visible on a 360×640 screen, with buttons below it (scrolling the page is fine **outside** the writing area).
- The stroke colour, outline and grid must be readable in both light and dark appearance.
- After a character has been loaded once, it works offline.

---

## 5. Storage and settings (`docs/js/storage.js`)

**Progress**
- Entries become `{ zv, vz, wr }`. Old entries without `wr` must keep working.
- `setLearned`: delete the entry only when all three are 0.
- `levelStats`: add `wr`; `any` = learned in any of the three.
- `importProgress`: accept `wr` and keep accepting old backups without it.
- Export is unchanged.

**Settings** — add:
- `writingOutline` (default `false`)
- `writingPinyin` (default `true`)

Both appear in Cài đặt under a "Luyện viết" heading:
- `Hiện chữ mờ khi bắt đầu`
- `Hiện pinyin khi luyện viết`

---

## 6. Tests

- Unit tests for `storage.js`: `wr` set/unset, stats, importing an old backup without `wr`.
- Playwright at 390×844:
  - level → `Luyện viết` → a 2-character word renders two boxes and a writing area
  - `Bỏ qua chữ này` twice → result line + card back + Đã thuộc/Chưa thuộc
  - mark learned → reload → that word doesn't come back in `wr`, but still does in `zv`/`vz`
  - card back `✍️ Viết` → sheet opens → `Đóng` → same card, same state
- Try to simulate a correct stroke by dispatching pointer events along the stroke's `medians` from the character data. If that turns out flaky, skip it and say so — Quan will test real drawing on his phone.
- Offline: load a word once, go offline (Playwright `context.setOffline(true)`), reopen it.
- Run the existing tests (`scripts/test_app.py`, `scripts/test_check.mjs`) — nothing else may break.

---

## 7. Done when

- All tests pass, the data build reports sizes and missing characters, and the feature is committed, pushed and live.
- **Checkpoint for Quan** — phone test list:
  1. Open the app (pull to refresh, or close and reopen, so the new version loads).
  2. HSK 1 → Luyện viết → write 3 words with your finger.
  3. Try `Xem cách viết`, `Hiện chữ mờ`, `Viết lại`, `Bỏ qua chữ này`.
  4. On a Trung → Việt card, tap `✍️ Viết`, write, close — you're back on the same card.
  5. Turn on airplane mode and write a word you've already opened — it still works.
- Log the version, sizes and any missing characters in `PROGRESS.md`.
