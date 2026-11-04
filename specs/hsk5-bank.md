# Phase 11 — Luyện đề: add the HSK 5 book (10 tests)

Add 10 HSK 5 mock tests to the encrypted question bank, using the **same pipeline as Phases 8 and 10** (`specs/mock-tests.md`, plus the lessons in `specs/hsk3-bank.md` and `PROGRESS.md`). Hard rules, units/types, extraction, audio cutting, encryption and cloud rules all apply unchanged. This file covers only what's different for HSK 5.

Prepared 2026-11-04 from the planning chat. The compact copy is already in the private repo `hsk-bank-private` at `materials/hsk5-book/`.

---

## 1. The material

**The book**
- **Title:** 新HSK五级全真模拟测试题集. The same series and layout as the HSK 4 book (`hsk4-book`).
- **Format:** HSK 2.0, **10 complete tests**, with listening scripts, answer keys and **explanations (答案说明, in Chinese)**.
- **Paper ids:** `hsk5-book-1` … `hsk5-book-10`. Title in the app: `Đề 1` … `Đề 10` under **HSK 5**. Bank levels become **[3, 4, 5]**.

**Pages:** `materials/hsk5-book/pages/p-NNN.jpg` = PDF page NNN, 200 dpi grayscale.
- Included: PDF page 17 (the 目录) and PDF pages 20–311.
- **PDF page = printed page + 17.** The source was a scanned PDF with no text layer, so read the page images visually.

**Page map** (from the 目录 — confirm it on p-017 before extracting):
| Test | Questions (PDF) | Listening script (PDF) | Answers (PDF) | Explanations (PDF start) |
|---|---|---|---|---|
| 1 | 20–36 | 192 | 198 | 199 |
| 2 | 37–53 | 203 | 209 | 210 |
| 3 | 54–70 | 216 | 222 | 223 |
| 4 | 71–87 | 227 | 232 | 233 |
| 5 | 88–104 | 239 | 245 | 246 |
| 6 | 105–121 | 251 | 257 | 258 |
| 7 | 122–138 | 263 | 269 | 270 |
| 8 | 139–155 | 274 | 280 | 281 |
| 9 | 156–172 | 286 | 292 | 293 |
| 10 | 173–191 | 297 | 304 | 305–311 |

Each test is 17 pages; test 10 runs to PDF 191. A test's explanations run until the next test's script starts.

---

## 2. ⚠️ Audio: identify which file is which test FIRST

`materials/hsk5-book/audio/src-00.mp3` … `src-09.mp3` (mono 64 kbps, 30–34 min each) came from 10 Ximalaya downloads that **carry no test number**. Their original names are listed in `audio/SOURCE.md`. The order is unknown: `src-00` (the file without a number) is *probably* test 1 and `src-0k` test k+1, but **don't assume it**.

Step 1 of this phase:
1. For each `src-NN`, transcribe the first few minutes with faster-whisper.
2. Match the first questions (第1题…) against the ten listening scripts (PDF 192, 203, …). The first dialogue of each test is distinct.
3. When every file maps to exactly one test, rename in `hsk-bank-private` with `git mv src-NN.mp3 testNN.mp3`.
4. Fill in the "Test" column of `SOURCE.md`, commit and push.
5. If a file matches no test, or two files match the same test, stop and tell Quan; one download may be missing or duplicated.

Also check each file for anything that isn't part of the exam (for example a platform intro or ad at the start or end). The cutting must skip it.

**HSK 5 listening plays each item ONCE** (verify on test 1), so there's normally no repeat to remove.

---

## 3. What goes into the bank, per test

| HSK 5 part | Questions | Bank tab | Type / unit |
|---|---|---|---|
| Listening part 1 | 1–20 | Nghe | `choice` A–D — a short dialogue plus the question; one clip each |
| Listening part 2 | 21–30 | Nghe | `choice` A–D — a longer dialogue; one clip each |
| Listening part 2 | 31–45 | Nghe | `choice` A–D — passages with 2–3 questions each. **One unit per passage**, with one clip for the passage plus its questions. Group by the script's "第X到Y题是根据下面一段话". |
| Reading part 1 | 46–60 | Đọc | **Cloze:** a passage with 3–4 numbered blanks, each blank has its own A–D options. **One unit per passage.** Show the passage with the blanks marked by their numbers, e.g. `（46）`, and the questions under it (the `choice` type with `context.text`, as for passages) |
| Reading part 2 | 61–70 | Đọc | `choice` A–D — a short text; choose the statement that matches it |
| Reading part 3 | 71–90 | Đọc | `choice` A–D — long passages with 4 questions each, **one unit per passage** |
| Writing part 1 | 91–98 | Sắp xếp câu | `order-words` — 8 per test; the answer comes from the key, and alternative orders from the explanations go in `alsoAccept` |
| Writing part 2 | 99–100 | — | **Skip** (essays) |

- **Expected per test: 98 questions** (Nghe 45 · Đọc 45 · Sắp xếp câu 8). **About 980 in all.**
- Decorative pictures next to reading passages aren't needed; skip them. HSK 5 has no picture-option questions.
- **Long passages:** check readability at 360 px (font ≥ 18 px, comfortable line height). The passage should stay visible or easy to scroll back to while answering its 4 questions. If it isn't, add a small "Xem lại bài đọc" (see the passage again) link above the questions.

---

## 4. Explanations

The book explains every answer, in Chinese.
- Store that as `explain_zh`.
- Fill `explain_vi` with a short Vietnamese version, written by Haiku in batches, as was done for HSK 4.
- Spot-check about 10 per test in the main session.

---

## 5. Size

- The bank is ≈ 101 MB today (HSK 4 ≈ 58, HSK 3 ≈ 44). HSK 5 will probably add 60–80 MB.
- `build_bank.py` already keeps unchanged files, so HSK 3 and 4 won't be rewritten. **Check this in the build output**: their files should show as unchanged.
- The `Tải toàn bộ đề về máy` button is per level, so its sizes must update for level 5.
- Bump the service-worker version; run the full test suite and the plaintext guard.

---

## 6. Order of work and checkpoints

1. **`git pull` both repos** (this phase's material and spec were added after Phase 10).
2. **Identify the audio files (section 2)** and check the page map against the 目录.
3. **Build `hsk5-book-1` end-to-end:**
   - extraction
   - explanations
   - clips
   - validation and `review.html`
   - encrypted bank with level 5 added
   - publish
4. **Checkpoint for Quan:**
   - Luyện đề → **HSK 5** on his phone.
   - A cloze passage and a long passage read well.
   - Clips match their questions.
   - HSK 3 and 4 are unchanged.
5. **Tests 2–10,** one at a time, with a short report each.
6. **Final report:**
   - totals per level and tab
   - bank size
   - anything excluded or any key oddities
   - **which repos (if any) have work on a `claude/...` branch that still needs merging into `main`**

Commit the work files to `hsk-bank-private` (`work/hsk5-book-N/`) as you go. Log everything in `PROGRESS.md`, but never the password or the magic link.
