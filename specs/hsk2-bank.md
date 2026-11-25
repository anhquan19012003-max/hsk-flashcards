# Phase 12 — Luyện đề: add the HSK 2 book (10 tests) — LOCAL sessions

Add 10 HSK 2 mock tests to the encrypted question bank with the same pipeline as Phases 8, 10 and 11 (`specs/mock-tests.md`, plus the lessons in `specs/hsk3-bank.md` and `PROGRESS.md`). This file covers only what's different.

Planned 2026-11-25 in the planning chat.

**This is the first bank phase run in normal Claude Code sessions on Quan's PC**, not a cloud session (the cloud credit has ended). Set-up steps: `setup/local-setup.md`.

---

## 1. The material

**The book**
- **Title:** 新汉语水平考试模拟试题集 HSK 二级 (the "xanh lá" series, same as the HSK 3 book), scanned by Tiếng Trung QTEDU.
- **Format:** HSK 2.0, **10 tests**.
- **Paper ids:** `hsk2-book-1` … `hsk2-book-10`. Title in the app: `Đề 1` … `Đề 10` under **HSK 2**. Bank levels become **[2, 3, 4, 5]**.

**Files on Quan's PC (the source; not in any repo):**
- PDF: `C:\Nick-Claude\Chinnese Learning App\HSK 2 sample test\HSK2 xanh lá.pdf` (261 pages, scanned at 288 dpi, no text layer).
- Audio: `…\HSK 2 sample test\File nghe HSK 2 xanh lá\（二级）01.mp3` … `10.mp3`. **The file number is the test number.** Check this on test 1 anyway.

**Page map** (PDF page = printed page + 20; confirm on the 目录, PDF p. 20):
| Test n | Questions (PDF) | Listening script (PDF) | Answer key (PDF) |
|---|---|---|---|
| n | `21 + 14·(n−1)` … +13 (test 1: 21–34 · test 10: 147–160) | `161 + 8·(n−1)` … +7 (test 1: 161–168 · test 10: 233–240) | `240 + n` (241 … 250) |

Answer sheets (PDF 251–260) are not needed. **There are no explanations in the book.**

---

## 2. ⚠️ Repo size — keep book material OUT of git this time

Sizes measured on 2026-11-25:
| | Now | Limit / guideline |
|---|---|---|
| `hsk-flashcards` repo (GitHub) | ≈ 170 MB | 1 GB recommended |
| Published site (`docs/`) | ≈ 172 MB (bank 164 MB: HSK 3 44, HSK 4 57, HSK 5 63) | 1 GB hard limit |
| `hsk-bank-private` repo (GitHub) | **≈ 600 MB** | 1 GB recommended |

- Before, the book copies (`materials/…`) went into `hsk-bank-private` only so cloud sessions could reach them. **A local session reads the originals straight from Quan's PC**, so:
  - Render pages and convert audio into `mock-tests/materials/hsk2-book/`, but **do not commit it**. Add `materials/hsk2-book/` to `hsk-bank-private/.gitignore` first and check it with `git check-ignore`.
  - Commit only the work outputs (`work/hsk2-book-N/`: `questions.json`, pictures, clips, `review.html`). Expected ≈ 50–60 MB in total, which keeps the private repo near 660 MB.
- **Expected growth of the public repo and site:** about +40–50 MB (HSK 3 was 44 MB with similar audio). That gives roughly 220 MB, well under the limits.
- In the final report, state the new sizes of both repos and of `docs/bank`.

---

## 3. What goes into the bank, per test

HSK 2 has **no writing section**, so there's no **Sắp xếp câu** for HSK 2. The app must hide that tab (or show it disabled with "Không có ở HSK 2") when a level has no questions of that skill.

| HSK 2 part | Questions | Tab | Type / unit |
|---|---|---|---|
| Listening part 1 | 1–10 | Nghe | `tf` with a **picture as the prompt**: hear a sentence, then decide whether the picture matches (✓/✗). Each question has its own picture and clip. |
| Listening part 2 | 11–20 | Nghe | **Picture matching**: two units (11–15, 16–20), with pictures A–F as `sharedOptions`; one clip per question (as in HSK 3 listening part 1). |
| Listening part 3 | 21–30 | Nghe | `choice` A/B/C: a short dialogue plus the question; text options with pinyin |
| Listening part 4 | 31–35 | Nghe | `choice` A/B/C: a slightly longer dialogue |
| Reading part 1 | 36–40 | Đọc | **Sentence → picture matching**: one unit with pictures A–F as `sharedOptions` (one is used by the example) |
| Reading part 2 | 41–45 | Đọc | `wordbank`: one unit, words A–F |
| Reading part 3 | 46–50 | Đọc | `tf`: a sentence plus a ★ statement, ✓/✗ |
| Reading part 4 | 51–60 | Đọc | **Sentence matching**: two units (51–55, 56–60), with sentences A–F / A–E as `sharedOptions` (as in HSK 3 reading part 1) |

- **Expected per test: 60 questions** (Nghe 35 · Đọc 25). **About 600 in all.**
- Skip the worked examples (例如).
- **HSK 2 pages print pinyin over the Chinese.** Keep it in the `pinyin` fields; the app already shows it.
- **Many pictures** (about 27 per test): crop each one cleanly to WebP ≤ 600 px. Check them on a 360 px phone screen; a tap should enlarge a picture.
- **Listening:** every item is **played twice** (verify on test 1). Keep one play; the 🔁 button replays it.

---

## 4. Explanations

The book has none, so do the same as for HSK 3: short Vietnamese `explain_vi` (1–2 sentences) written by the Haiku subagent in batches, with a one-line Vietnamese gist of the listening dialogue. Spot-check about 10 per test.

---

## 5. Working locally — differences from the cloud runs

- **Paths.** The material is read from Quan's PC folder (section 1). The public repo and `mock-tests/` (the private repo) live where `setup/local-setup.md` puts them.
- **Password.** It comes from `mock-tests/.bank-password` (never committed). `build_bank.py` refuses a password that doesn't match the existing bank — if it refuses, stop and ask Quan; **never use `--new-salt`** unless he asks for a new password.
- **Speech recognition** runs on the PC's CPU. Use a faster-whisper model that keeps a test under about 15 minutes (`small`, int8). Use `medium` only for a part where `small` is clearly wrong. Process one test at a time.
- **Usage.** Quan's normal plan limits apply. Reading the page images is the expensive part. Work **one test per session**, and save and push after each test. If a session gets long, stop cleanly and say where to continue. Use Haiku for explanations as before.
- **Pushing.** Push straight to `main` (there's no `claude/…` branch problem locally), but only after the full tests and the plaintext guard pass. `git config core.hooksPath .githooks` must be set on this PC (the setup guide does it).

---

## 6. App changes (small)

- **Levels:** Luyện đề shows **HSK 2, 3, 4, 5** in order.
- **Hide empty skill tabs per level** (HSK 2 has no Sắp xếp câu).
- **Picture-prompt `tf`:** a picture as the prompt for a ✓/✗ question. Check whether the engine supports it; if not, add it, with a unit test and a Playwright check.
- **Bump the service-worker version.** Make sure the per-level download sizes include level 2.

---

## 7. Order of work and checkpoints

1. **Set-up check** (`setup/local-setup.md` step 5): both repos pulled, tools working, password file present, hooks on.
2. **Prepare:**
   - ignore `materials/hsk2-book/` in the private repo
   - render pages 20–250 at 200 dpi grayscale into it
   - convert the audio to mono 64 kbps MP3 there
   - check the page map against the 目录
   - check the audio of test 1 (two plays per item, file 01 = test 1)
3. **Build `hsk2-book-1` end-to-end:**
   - extraction, with picture crops
   - explanations
   - clips
   - validation and `review.html`
   - encrypted bank with level 2
   - app tweaks (section 6)
   - tests and plaintext guard
   - push
4. **Checkpoint for Quan:**
   - **HSK 2** shows in Luyện đề on his phone, with only the Nghe and Đọc tabs.
   - Pictures are clear (✓/✗ picture questions, matching).
   - Clips match their questions.
   - HSK 3, 4 and 5 are unchanged.
5. **Tests 2–10**, one per session if needed, each with a short report.
6. **Final report:**
   - totals
   - excluded questions and key oddities
   - repo and site sizes (section 2)

Log everything in `PROGRESS.md`, but never the password or the magic link.
