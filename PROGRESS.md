# PROGRESS

## Status
Phase 9 (Part A published; **Part B Trắc nghiệm built, tested and published — checkpoint: waiting for Quan's phone test**, see "Waiting on Quan"). Phase 8 (Luyện đề) is done and phone-tested (all 10 HSK 4 papers, 950 questions, in the encrypted bank). Phase 7 is done.

## Done
- 2026-10-30 Phase 0: git repo, `.gitignore`, `example-writer` (Haiku) agent copied.
- 2026-10-30 Phase 1: `data/raw` for 4,545 words; Hán Việt from Wiktionary (+ Unihan fallback), review files exported.
- 2026-10-30 Phase 2: app first version (home, level, study, review, settings, PWA, offline); 29 Playwright checks.
- 2026-10-30 Phase 3: HSK1 example sentences (Haiku) + review.
- 2026-10-30 Phase 4: example sentences for HSK2–5, `pos` filled for HSK4–5; `docs/data/hsk1–5.json` rebuilt.
- 2026-10-30 Phase 5: GitHub repo `anhquan19012003-max/hsk-flashcards`, Pages from `main` / `docs`; iPhone install, audio and offline tested by Quan.
- 2026-10-30 Voice dropdown in Cài đặt (picks among the phone's zh voices).
- 2026-10-30 Phase 7: Luyện viết — see "Phase 7 details"; Quan tested on iPhone (drawing, animation, outline, restart, skip, card-back sheet, offline): all good.

- 2026-10-30 Luyện viết: strokes now accepted in ANY order (custom grading, `docs/js/strokematch.js`); sw version 5.

- 2026-10-30 Phase 8 step 1 (engine, fixture only): `docs/js/bank*.js` (Web Crypto unlock by password or `#k=` magic link, key in IndexedDB; Luyện đề screens; 3 tabs Nghe / Đọc / Sắp xếp câu; progress `hskfc.v1.bank`; backup/restore `_bank`; `Tải toàn bộ đề về máy`, `Khóa lại`), service worker v6 with cache `hskfc-bank`, `scripts/bank/` (build_bank, bankcrypto, validate_paper, guard, make_fixture), fixture in `scripts/fixtures/`, GitHub Actions workflow `.github/workflows/guard.yml` (plaintext guard on every push), pre-commit hook `.githooks/pre-commit`. Tests: `bash scripts/run_tests.sh` (bank unit 40, bank JS 24, bank browser 56, app 29, writing 28, plus the older Node tests, and the plaintext guard first and last).

- 2026-10-30 Phase 8: Đề 2 added (95 questions, 40 clips: min recall 0.94 / precision 0.94, 0 excluded). The book's key prints Q47 as C but its own explanation and the sentence give D (留); the bank uses D (noted in `review.html`). Bank now 190 questions, 80 clips, 11.7 MB. Tooling is per paper: `work/make_questions.py N`, `prepare_explain.py N`, `merge_explain.py N`, `cut_clips.py N`, `verify_clips.py N`, `make_review.py N`; the Whisper transcripts of tests 2–10 are made by `scratchpad/queue.sh` (they are not in git: `work/_audio/` is only on the cloud machine unless committed).

- 2026-10-30 Phase 8: Đề 3 added (95 questions, 40 clips: min recall 0.93 / precision 0.94, 0 excluded; Whisper missed the start of Q33, placed from silence boundaries in `clip_overrides.json`). Bank now 285 questions, 120 clips, 17.1 MB.
- 2026-10-30 Phase 8: Đề 4 added (95 questions, 40 clips, all 40 verified, 0 flagged). Bank now 380 questions, 160 clips, 24.0 MB. Order-words Q90/Q94 carry the alternative answers printed in the book.
- 2026-10-30 Phase 8: Đề 5 added (95 questions, 40 clips, all verified, 0 flagged). Bank now 475 questions, 200 clips, 29.8 MB.
- 2026-10-30 Phase 8: Đề 6 added (95 questions, 40 clips verified, 0 flagged; Q28 and Q30 placed from silence boundaries in `clip_overrides.json`). Bank now 570 questions, 240 clips, 35.5 MB.
- 2026-10-30 Phase 8: Đề 7 added (95 questions, 40 clips verified, 0 flagged; Q5 and Q22 placed from timestamps in `clip_overrides.json` because Whisper garbled them). Order-words Q87: the printed tile “又……又……” is split into two “又” tiles so the sentence can be built. Bank now 665 questions, 280 clips, 41.3 MB.
- 2026-10-30 Phase 8: Đề 8 added (95 questions, 40 clips verified, 0 flagged). Bank now 760 questions, 320 clips, 46.7 MB.
- 2026-10-30 Phase 8: Đề 9 added (95 questions, 40 clips; clip 36–37 tripped the length heuristic at 45.9 s but recall/precision are 1.00, accepted by hand). Bank now 855 questions, 360 clips, 52.3 MB.
- 2026-10-30 Phase 8: Đề 10 added (95 questions, 40 clips verified, 0 flagged; Q18 timestamps pinned in `clip_overrides.json`). **All 10 HSK 4 papers done**: bank 950 questions, 400 clips, 57.9 MB; all tests and the plaintext guard pass.
- 2026-10-30 Phase 9 Part A (published, sw v7): (A1) Cài đặt now waits for the saved bank key and `meta.json` before drawing, so the `Luyện đề` section (download + `Khóa lại`) shows whenever the bank is unlocked on this device (the old start-up refresh is gone). (A2) `Tải toàn bộ đề về máy` on the Luyện đề screen below the level list: shows the size and “nên dùng Wi-Fi”, says it is optional; once every clip is in the cache both places show `Đã tải về máy ✓`. New test `scripts/test_bank_download.py` (11 checks, in `run_tests.sh`); `test_bank.py` / `test_writing.py` adjusted for the slightly later Cài đặt draw.
- 2026-10-30 Phase 9 Part B (published, sw v8): `Trắc nghiệm 📝` on every level screen (between Luyện viết and Ôn lại). Pure generator `docs/js/quizcore.js` (seeded RNG; 6 types nghĩa / chữ Hán / pinyin / nghe / điền từ / Hán Việt; hard rules: 4 distinct options, one correct, no same hanzi / accept-list / shared-meaning wrong option, no toneless homophone for nghe, tone-variant pinyin distractors; soft preference same level → same pos → same length → shared character), UI `docs/js/quiz.js` (setup with type chips, Tất cả từ / Chỉ từ đã thuộc, size 10/20/50/Tất cả; Câu mới / Làm lại câu sai / Làm lại từ đầu; A–D options, red/green feedback, compact word card with example, `Thêm vào ôn tập`, summary with wrong-word list), shared card markup `docs/js/wordcard.js`, storage `hskfc.v1.quiz` (`{ok, wrong}` per word id; backup key `_quiz`, left out while empty; old backups leave quiz progress alone), settings `quizTypes` / `quizPool` / `quizSize`, `hasChineseVoice()` (nghe hidden with a hint when no zh voice). Tests: `test_quizcore.mjs` (17 checks; 54,492 questions = 4,545 words × every valid type, all hard rules hold), `test_quiz.py` (55 browser checks at 390×844 incl. offline and no-voice), `test_storage.mjs` extended; all in `run_tests.sh`, plus the whole existing suite and the plaintext guard pass.
  - Generator report (seed 1): lower-level fallback was needed for only **4 of 27,246 generated questions** (one per word × type) (HSK4: 2, HSK5: 2; HSK1–3: 0). Words that cannot get a type: `dientu` 2 words (example doesn't contain the word exactly), `hanviet` 22 words (no Hán Việt reading); every other type is available for all 4,545 words.

## Phase 8 details
- Code: `docs/js/bank.js` (UI), `bankcore.js` (pure logic), `bankcrypto.js` (Web Crypto). Build side: `scripts/bank/`. Private work files: repo `hsk-bank-private` (`work/<paper-id>/`).
- Encrypted files in `docs/bank/`: `meta.json` (format, salt, iterations, levels, check) + `hsk4/index.bin` + `hsk4/m/<hash>.bin`. The plaintext guard (`python scripts/bank/guard.py`) fails on anything readable there; it also runs in CI and in the pre-commit hook (`git config core.hooksPath .githooks`).
- Tests of the engine serve `scripts/fixtures/bank/` as `/bank/` (password `test-password`; made-up content only).
- Running tests in the cloud container: the pip Playwright needs the pre-installed browser; `scripts/browser.py` handles it.

- 2026-10-30 Phase 8 step 3: `hsk4-book-1` built end-to-end in the cloud: 95 questions (Nghe 45 · Đọc 30 · Sắp xếp câu 20), 40 audio clips (one per question; two-question passages share a clip), all clips re-transcribed and checked against the book's script (min recall 0.85, min precision 0.88; 0 flagged, 0 excluded), `explain_zh` from the book + `explain_vi` by Haiku (the 10 word-ordering items of writing part 1 have a hand-written Vietnamese note with the translation). Encrypted bank in `docs/bank/` (42 files, 5.4 MB). Work files are in the private repo `work/hsk4-book-1/` (`questions.json`, `clips/`, `review.html`) with the tooling in `work/` (`cut_clips.py`, `verify_clips.py`, `make_review.py`).

## Phase 7 details
- Library: Hanzi Writer **3.7.3** (`docs/vendor/hanzi-writer.min.js`, 37 KB, MIT; licence in `docs/vendor/LICENSE-hanzi-writer.txt`). Loaded on first use, no CDN.
- Stroke data: `hanzi-writer-data` **2.0.1** (Make Me a Hanzi, Arphic Public License: `docs/vendor/ARPHICPL.TXT`).
  `scripts/build_hanzi_data.py` (called from `scripts/build.py`) copies only the characters used in HSK1–5:
  **1,590 characters, 1,590 files, 3.9 MB; characters with no data: none.** The npm package (~50 MB) is downloaded once
  into `data/cache/` (git-ignored) and only when a character is missing from `docs/hanzi/`.
- Service worker: version **5** (was 4 before the order-free change). New cache `hskfc-hanzi` (cache-first, filled on first use, kept across versions); the
  library and `js/writing.js` are in the app shell. The 1,590 data files are NOT precached.
- App: `Luyện viết ✍️` on the level screen (third direction `wr`, own learned status, review picker has 3 choices),
  `✍️ Viết` on every card back (full-screen sheet; does not change progress), two settings under "Luyện viết"
  (`writingOutline`, `writingPinyin`), licence line in Cài đặt.
- Progress shape: `{zv, vz}` plus `wr: 1` only when learned in writing (entries without `wr` stay valid; old backups import unchanged).
- Tests: `scripts/test_storage.mjs` (new), `scripts/test_check.mjs`, `scripts/test_app.py` (29), `scripts/test_writing.py` (28, now incl. reversed/shuffled stroke order and a wrong line), `scripts/test_strokematch.mjs` (all 1,590 characters, shuffled + noisy strokes accepted; wrong/backwards lines rejected;
  includes simulated strokes along the stroke medians — they were accepted — and an offline run). All pass.
- Layout checked at 360×640: the writing square ends at ~555 px, action buttons start right below it.

## Waiting on Quan
- **Phase 9 checkpoint (Trắc nghiệm):** (1) close and reopen the app to get the new version (sw v8); (2) HSK 1 → `Trắc nghiệm 📝` → do a set of 10 with all types; (3) try `Chỉ từ đã thuộc` and turn a few types off; (4) get one wrong on purpose, then `Làm lại câu sai`; (5) on a word you learned in flashcards, get it wrong and tap `Thêm vào ôn tập` → it comes back in Trung → Việt; (6) listening type: tap 🔊 and hear the word. Also check `Cài đặt` shows the Luyện đề section (download + `Khóa lại`) and the new `Tải toàn bộ đề về máy` on the Luyện đề screen.
- **Phase 8 checkpoint (all 10 HSK 4 papers):** (1) open the app, tap `📝 Luyện đề`, unlock with the magic link (and on another browser with the password); (2) try the three tabs (Nghe, Đọc, Sắp xếp câu), a few audio clips from different papers, and `Làm câu mới` / `Làm lại câu sai`; (3) on the laptop `git pull` in `mock-tests/` and open `mock-tests/work/hsk4-book-N/review.html` for a spot check (flagged items first); (4) tell me what the iPhone home-screen app does (still unlocked after opening the link in Safari?); (5) check the book-key notes under Known issues; (6) say whether to send the Zalo message to friends (draft is in my last chat reply).
Phone check of the any-order writing (draw strokes out of order; wrong lines still rejected). Nothing blocking. Still open from before: review of the HSK2–5 spreadsheets in `review/` (tell me "I reviewed HSK N" and I import them).

## Decisions
- 2026-10-30 (Phase 9) Trắc nghiệm progress is per word, not per type: a correct answer sets `ok: 1` (leaves `Làm câu mới`), a wrong one `ok: 0, wrong+1` (appears in `Làm lại câu sai`). It never changes flashcard progress by itself; only `Thêm vào ôn tập` (shown after a wrong answer on a word learned in a flashcard direction) clears `zv` and `vz`.
- 2026-10-30 (Phase 9) The quiz keeps its own set size (`settings.quizSize`, default 20) so changing it does not alter the flashcard session size.
- 2026-10-30 (Phase 9) Words learned in any direction (`zv`, `vz` or `wr`) count as learned for the `Chỉ từ đã thuộc` pool.
- 2026-10-30 (Phase 8) Where the book's printed key contradicts the book's own explanation or text, the key was changed to match the explanation: Đề 7 Q10 → ✗, Đề 10 Q4 → ✗. Đề 10 Q89: the book's answer has an extra “的” that is not among its tiles, so the answer is “这道题的答案就在书后面。”. Đề 7 Q87: tile “又……又……” split into two “又”. Đề 8 Q69 key (D) is kept although it does not match the passage; flagged for Quan.
- 2026-10-30 (Phase 8) Both ordering types (`order-sentences`, `order-words`) live in the third tab, `Sắp xếp câu`; units use `skill` = `nghe` | `doc` | `sapxep`.
- 2026-10-30 (Phase 8) Bank progress travels in the existing backup file under one extra key `_bank` (left out while empty). A backup without `_bank` restores the words and leaves the bank progress on the device alone.
- 2026-10-30 (Phase 8) `meta.json` is fetched only when Luyện đề is opened (or when a key is already saved), so the live site makes no request for it otherwise.
- 2026-10-30 (Phase 8) An answer given to a question that was already correct counts like any other: wrong → `ok: 0`, it comes back in `Làm lại câu sai`.
- 2026-10-30 (Phase 8) `Câu của mình cũng đúng` is offered for both ordering types and undoes the wrong mark just recorded.
- 2026-10-30 Haiku stays for example sentences; out-of-level characters and duplicate sentences are acceptable (HSK5 has 129 duplicates, ~10%); Hán Việt need not be perfect; words with an unresolved Hán Việt reading show no Hán Việt line.
- 2026-10-30 Public GitHub repo, including `source/vocab.xlsx` and the review files (Quan: "the source is published anyway"); `data/unihan/` is not committed.
- 2026-10-30 Writing practice (Phase 7): its own mode on the level screen **and** a button on every card back; same random/skip-learned logic with its own status.
- 2026-10-30 Writing result counts only the completed attempt of each character (mistakes from a restarted attempt, or while watching the animation, are not added up).
- 2026-10-30 `wr` is stored only when 1 (keeps old entries and backups identical).
- 2026-10-30 Luyện viết grades strokes in any order (Quan: the strict order was too strict). Each drawn line must still match a stroke's shape and direction; Hanzi Writer's quiz is no longer used (only its outline + animation). A wrong line counts as 1 mistake; hint (one missing stroke flashes) after 3 wrong lines in a row.

## Known issues
- 2026-10-30 Phase 8 book-key notes for Quan: Đề 7 Q10 and Đề 10 Q4: book key ✓ contradicts the book's own explanation → used ✗; Đề 8 Q69 printed key D does not match the passage (kept book key, flag for review); Đề 9 Q42 answer is by elimination; Đề 10 Q57/Q58 explanation letters in the book do not match the key ACB → explanation re-lettered to the key.
- Phase 8: the CJK clips come from the 128 kbps → 64 kbps compact copy, re-encoded mono 48 kbps; the page map could not be checked against the 目录 (PDF p. 15 is not in the compact copy) but Test 1's start (p. 17), script (p. 179), answers (p. 185) and explanations (p. 186–195) matched the spec.
- Phase 8: the GitHub Actions guard cannot stop GitHub Pages from deploying (Pages publishes `main/docs` by itself); it flags the push as failed, and the pre-commit hook (`git config core.hooksPath .githooks`) stops it earlier on a laptop.
- Phase 8: writing part 2 (look at the picture and write a sentence, Q96–100) is skipped as agreed.
- Hán Việt: ~16 words have no reading (blank in the app); ~60–130 more are flagged `hanviet_check` in the review files.
- HSK5: 129 duplicate example sentences; ~40–50 sentences per level use characters above the card's level (accepted).
- Fixed on the way: a 'Chưa thuộc' card used to come back 6–9 cards later instead of 5–8 (it now returns as the 5th–8th card).
- Backup download from the home-screen app on iPhone is untested.
