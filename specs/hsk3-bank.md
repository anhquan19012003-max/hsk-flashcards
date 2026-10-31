# Phase 10 — Luyện đề: add the HSK 3 book (10 tests)

Add 10 HSK 3 mock tests to the existing encrypted question bank, using the **same pipeline as Phase 8** (`specs/mock-tests.md`). Read that spec first: hard rules (section 0), units and types (2), extraction (3), audio cutting (4), encryption (5) and the cloud rules (11) all apply unchanged. This file only covers what's different for HSK 3.

Prepared 2026-10-31 from the planning chat. The compact copy of the book is already in the private repo `hsk-bank-private`, at `materials/hsk3-book/`.

---

## 1. The material

**The book**
- **Title:** 新汉语水平考试模拟试题集 HSK 三级 (BLCUP; a Vietnamese reprint by "Học Bá HSK").
- **Format:** HSK 2.0, **10 complete tests**, the same series as the HSK 4 book.
- **Paper ids:** `hsk3-book-1` … `hsk3-book-10`. Title shown in the app: `Đề 1` … `Đề 10`, under **HSK 3**. Level 3 is its own bank level, separate from the HSK 4 tests.

**Pages:** `materials/hsk3-book/pages/p-NNN.jpg` = PDF page NNN, 200 dpi grayscale. **PDF page = printed page + 20.** The source was a scanned PDF with no text layer, so read the page images visually.

**Page map** (from the book's 目录 on PDF page 20 — confirm before extracting):
| Test | Questions (PDF pages) | Listening script (PDF start) | Answer key (PDF page) |
|---|---|---|---|
| 1 | 21–34 | 161 | 221 |
| 2 | 35–48 | 167 | 222 |
| 3 | 49–62 | 173 | 224 |
| 4 | 63–76 | 179 | 225 |
| 5 | 77–90 | 185 | 226 |
| 6 | 91–104 | 191 | 228 |
| 7 | 105–118 | 197 | 229 |
| 8 | 119–132 | 203 | 231 |
| 9 | 133–146 | 209 | 232 |
| 10 | 147–160 | 215 | 233 |

- Each test is 14 pages.
- A script or key runs until the next test's start. Test 10's script ends at 220, and its key ends at 234.
- Answer sheets (PDF 235+) aren't included and aren't needed.

**Audio:** `materials/hsk3-book/audio/testNN.mp3` — mono 64 kbps, about 40 minutes per test (37–42).
- **Every item is played TWICE** (the script says 一共10个题，每题听两次). Section 4 step 3 of the mock-tests spec ("one play only") applies: keep the first play and cut before the repeat. Verify on test 1.
- Each part starts with instructions and a worked example (例如) — skip those.
- The originals stay on Quan's PC (`C:\Nick-Claude\Chinnese Learning App`).

**No explanations in this book.** Unlike the HSK 4 book, it has only the answer key and the listening scripts. See section 3.

---

## 2. What goes into the bank, per test

| HSK 3 part | Questions | Bank tab | Type / unit |
|---|---|---|---|
| Listening part 1 | 1–10 | Nghe | Picture matching. **Two units**, 1–5 and 6–10. Each unit's `sharedOptions` are the pictures A–F (cropped, WebP ≤ 600 px). Each question has its own clip (a short dialogue). Use type `choice`; the engine already shows picture options in a grid. Group 1 includes the example's picture (its answer is printed on the page). Keep all printed pictures as options, since that's how the real test works. |
| Listening part 2 | 11–20 | Nghe | `tf` — hear a sentence; the printed statement (★…) is the prompt; ✓/✗ |
| Listening part 3 | 21–30 | Nghe | `choice` A/B/C — a short dialogue plus the question read aloud |
| Listening part 4 | 31–40 | Nghe | `choice` A/B/C — a longer dialogue plus the question |
| Reading part 1 | 41–50 | Đọc | Sentence matching. **Two units** (41–45, 46–50), each with shared options A–F (sentences). Reuse the `wordbank` layout (options listed once at the top), but use the instruction "Chọn câu phù hợp". The example in group 1 uses up one option. |
| Reading part 2 | 51–60 | Đọc | `wordbank` — **two units**, each with its own word list A–F |
| Reading part 3 | 61–70 | Đọc | `choice` A/B/C — a short text plus a ★ question |
| Writing part 1 | 71–75 | Sắp xếp câu | `order-words` — arrange the printed words into a sentence; the answer comes from the key |
| Writing part 2 | 76–80 | — | **Skip** (write the character for the given pinyin — not multiple choice) |

- **Expected per test: 75 questions** (Nghe 40 · Đọc 30 · Sắp xếp câu 5). **About 750 in all.**
- **HSK 1–3 pages print pinyin.** Where the page prints pinyin over the text, keep it in `pinyin` fields so the app can show it, as the spec allows.

---

## 3. Explanations

The book gives no explanations. Generate **short Vietnamese explanations** (`explain_vi`, 1–2 sentences) with a Haiku subagent, as cheap batches:
- Say why the answer is right, quoting the key words from the script or passage. For listening, add a one-line Vietnamese gist of what was said.
- Leave `explain_zh` empty. The app already hides the toggle when it's missing; check this.
- Spot-check about 10 per test in the main session. If Haiku is poor here, tell Quan and propose Sonnet for this step only.

(Quan can turn explanations off at the checkpoint.)

---

## 4. App changes (small)

- **Levels:** the Luyện đề level list shows **HSK 3** and **HSK 4**. `meta.json` `levels` becomes `[3, 4]`; the level index is `docs/bank/hsk3/index.bin`, with media under `docs/bank/hsk3/m/`.
- **Sizes:** check the `Tải toàn bộ đề về máy` size and wording now that there are two levels. Show the total, or offer a per-level download if that's simple.
- **Picture options:** check they look right on a 360 px-wide phone (6 pictures, 2 or 3 per row, readable letters), and that a picture can be enlarged with a tap if it's small.
- **Bump the service-worker version.** Run the full test suite, including the plaintext guard.

---

## 5. Order of work and checkpoints

1. **Check the inputs:** the page map against the 目录 (PDF p. 20); the audio of test 1 (two plays per item); the password from `BANK_PASSWORD`.
2. **Build `hsk3-book-1` end-to-end:**
   - extraction, with picture crops
   - explanations
   - clips (one play each)
   - validation and `review.html`
   - encrypted bank, with level 3 added next to level 4
   - publish
3. **Checkpoint for Quan:**
   - Open Luyện đề → **HSK 3** on his phone.
   - In Nghe part 1, the pictures are clear and the clips match.
   - Try Đọc and Sắp xếp câu.
   - Read a few Vietnamese explanations.
   - Confirm HSK 4 still works exactly as before.
4. **Tests 2–10,** one at a time, with a short report for each (questions, clips flagged or excluded, key oddities).
5. **Final report:**
   - totals per level and tab
   - bank size
   - anything excluded and why
   - **which repos (if any) have work on a `claude/...` branch that still needs merging into `main`**

Commit the work files to `hsk-bank-private` (`work/hsk3-book-N/`) as you go. Log everything in `PROGRESS.md`, but **never the password or the magic link**.
