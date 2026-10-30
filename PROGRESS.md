# PROGRESS

## Status
Phase 7 (Luyện viết / writing practice): built, tested, pushed. **Waiting for Quan's phone test** (checklist below).

## Done
- 2026-10-30 Phase 0: git repo, `.gitignore`, `example-writer` (Haiku) agent copied.
- 2026-10-30 Phase 1: `data/raw` for 4,545 words; Hán Việt from Wiktionary (+ Unihan fallback), review files exported.
- 2026-10-30 Phase 2: app first version (home, level, study, review, settings, PWA, offline); 29 Playwright checks.
- 2026-10-30 Phase 3: HSK1 example sentences (Haiku) + review.
- 2026-10-30 Phase 4: example sentences for HSK2–5, `pos` filled for HSK4–5; `docs/data/hsk1–5.json` rebuilt.
- 2026-10-30 Phase 5: GitHub repo `anhquan19012003-max/hsk-flashcards`, Pages from `main` / `docs`; iPhone install, audio and offline tested by Quan.
- 2026-10-30 Voice dropdown in Cài đặt (picks among the phone's zh voices).
- 2026-10-30 Phase 7: Luyện viết — see "Phase 7 details".

## Phase 7 details
- Library: Hanzi Writer **3.7.3** (`docs/vendor/hanzi-writer.min.js`, 37 KB, MIT; licence in `docs/vendor/LICENSE-hanzi-writer.txt`). Loaded on first use, no CDN.
- Stroke data: `hanzi-writer-data` **2.0.1** (Make Me a Hanzi, Arphic Public License: `docs/vendor/ARPHICPL.TXT`).
  `scripts/build_hanzi_data.py` (called from `scripts/build.py`) copies only the characters used in HSK1–5:
  **1,590 characters, 1,590 files, 3.9 MB; characters with no data: none.** The npm package (~50 MB) is downloaded once
  into `data/cache/` (git-ignored) and only when a character is missing from `docs/hanzi/`.
- Service worker: version **4**. New cache `hskfc-hanzi` (cache-first, filled on first use, kept across versions); the
  library and `js/writing.js` are in the app shell. The 1,590 data files are NOT precached.
- App: `Luyện viết ✍️` on the level screen (third direction `wr`, own learned status, review picker has 3 choices),
  `✍️ Viết` on every card back (full-screen sheet; does not change progress), two settings under "Luyện viết"
  (`writingOutline`, `writingPinyin`), licence line in Cài đặt.
- Progress shape: `{zv, vz}` plus `wr: 1` only when learned in writing (entries without `wr` stay valid; old backups import unchanged).
- Tests: `scripts/test_storage.mjs` (new), `scripts/test_check.mjs`, `scripts/test_app.py` (29), `scripts/test_writing.py` (25, new;
  includes simulated strokes along the stroke medians — they were accepted — and an offline run). All pass.
- Layout checked at 360×640: the writing square ends at ~555 px, action buttons start right below it.

## Waiting on Quan
Phone test of Luyện viết (reopen the app so version 4 loads: close it fully and open it again; if it still looks old, once more):
1. HSK 1 → Luyện viết → write 3 words with your finger.
2. Try `Xem cách viết`, `Hiện chữ mờ`, `Viết lại`, `Bỏ qua chữ này`.
3. On a Trung → Việt card, flip it, tap `✍️ Viết`, write, `Đóng` — you should be back on the same card.
4. Turn on airplane mode and write a word you've already opened — it should still work.
Also pending from before: reviewing the HSK2–5 review spreadsheets (nothing imported yet; only HSK1 was reviewed).

## Decisions
- 2026-10-30 Haiku stays for example sentences; out-of-level characters and duplicate sentences are acceptable (HSK5 has 129 duplicates, ~10%); Hán Việt need not be perfect; words with an unresolved Hán Việt reading show no Hán Việt line.
- 2026-10-30 Public GitHub repo, including `source/vocab.xlsx` and the review files (Quan: "the source is published anyway"); `data/unihan/` is not committed.
- 2026-10-30 Writing practice (Phase 7): its own mode on the level screen **and** a button on every card back; same random/skip-learned logic with its own status.
- 2026-10-30 Writing result counts only the completed attempt of each character (mistakes from a restarted attempt, or while watching the animation, are not added up).
- 2026-10-30 `wr` is stored only when 1 (keeps old entries and backups identical).

## Known issues
- Hán Việt: ~16 words have no reading (blank in the app); ~60–130 more are flagged `hanviet_check` in the review files.
- HSK5: 129 duplicate example sentences; ~40–50 sentences per level use characters above the card's level (accepted).
- Fixed on the way: a 'Chưa thuộc' card used to come back 6–9 cards later instead of 5–8 (it now returns as the 5th–8th card).
- Not tested on a real phone yet: finger drawing, `touch-action`/overscroll behaviour on iOS Safari, 🔊 with the new layout.
- Backup download from the home-screen app on iPhone is untested.
