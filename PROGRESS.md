# PROGRESS

## Status
Phase 8 (Luyện đề, question bank): engine published; `hsk4-book-1` (Đề 1, 95 questions) is in the encrypted bank. **Checkpoint: waiting for Quan's phone test** (see "Waiting on Quan"). Đề 2 is also in the bank (2026-10-30); Đề 3 is partly transcribed in the private repo (`work/hsk4-book-3/`, TODO list at the end of `content_part1.py`); Đề 4–10 not started. Phase 7 is done (Quan's phone check of the any-order writing is still open).

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
- **Phase 8 checkpoint (Đề 1):** (1) open the app, tap `📝 Luyện đề`, unlock with the magic link and, on another browser, with the password; (2) try the three tabs (Nghe, Đọc, Sắp xếp câu) incl. `Câu của mình cũng đúng`; (3) listen to some clips; (4) on the laptop `git pull` in `mock-tests/` and open `mock-tests/work/hsk4-book-1/review.html` (flagged items first; Q67 has a transcription note); (5) tell me what happens on the iPhone home-screen app (is it still unlocked after opening the link in Safari?). Also decide: keep the Chinese explanation toggle? Then say "continue" for Đề 2–10.
Phone check of the any-order writing (draw strokes out of order; wrong lines still rejected). Nothing blocking. Still open from before: review of the HSK2–5 spreadsheets in `review/` (tell me "I reviewed HSK N" and I import them).

## Decisions
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
- Phase 8: the CJK clips come from the 128 kbps → 64 kbps compact copy, re-encoded mono 48 kbps; the page map could not be checked against the 目录 (PDF p. 15 is not in the compact copy) but Test 1's start (p. 17), script (p. 179), answers (p. 185) and explanations (p. 186–195) matched the spec.
- Phase 8: the GitHub Actions guard cannot stop GitHub Pages from deploying (Pages publishes `main/docs` by itself); it flags the push as failed, and the pre-commit hook (`git config core.hooksPath .githooks`) stops it earlier on a laptop.
- Phase 8: writing part 2 (look at the picture and write a sentence, Q96–100) is skipped as agreed.
- Hán Việt: ~16 words have no reading (blank in the app); ~60–130 more are flagged `hanviet_check` in the review files.
- HSK5: 129 duplicate example sentences; ~40–50 sentences per level use characters above the card's level (accepted).
- Fixed on the way: a 'Chưa thuộc' card used to come back 6–9 cards later instead of 5–8 (it now returns as the 5th–8th card).
- Backup download from the home-screen app on iPhone is untested.
