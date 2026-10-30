# Phase 9 — Small fixes + Trắc nghiệm (vocab multiple-choice quiz)

Read the whole spec before starting. Part A first (small, cheap), then Part B.

---

## Part A — Small fixes

**A1. The Luyện đề section in Cài đặt**
- Today the section (with `Tải toàn bộ đề về máy` and `Khóa lại`) only appears if Luyện đề was opened earlier in the same visit. `bank.settingsSection()` returns `""` until `meta` is loaded.
- Fix: when Cài đặt opens and a key is saved, load `meta` first (or show the section as soon as it arrives). The section must appear whenever the bank is unlocked on this device.

**A2. A `Tải toàn bộ đề về máy` shortcut on the Luyện đề screen**
- Put a small button below the level list.
- Its dialog shows the total size (≈58 MB) and says "Nên dùng Wi-Fi".
- If everything is already cached, show `Đã tải về máy ✓` instead.
- Make clear it's optional: one line saying that without it, listening clips download the first time each question is used.

Test both, publish, and log them in `PROGRESS.md`.

---

## Part B — Trắc nghiệm (multiple-choice vocab quiz)

A multiple-choice quiz **generated automatically from the existing word data** (`docs/data/hsk{N}.json`). It needs no new content, no generated text and no encryption (the vocab data is already public), and it works fully offline. It reuses the look and logic of the Luyện đề question screens.

Quan's decisions (2026-10-30):
1. **All six question types** (table below), including Hán Việt.
2. **Which words:** a toggle, **Tất cả từ** (default) / **Chỉ từ đã thuộc** (words learned in any flashcard direction: `zv`, `vz` or `wr`).
3. **Separate from flashcards.** Quiz results never change flashcard progress automatically. A small optional `Thêm vào ôn tập` button puts a word back into flashcard study (details below).
4. **Name:** `Trắc nghiệm`.

### B1. Where it appears
- On each **level screen**, add a fourth button: `Trắc nghiệm 📝` with `Còn N từ chưa làm đúng`. Place it after `Luyện viết ✍️`, before `Ôn lại từ đã thuộc`.
- It uses only that level's words for the questions. Wrong options may borrow from lower levels if a level runs short (see B3).

### B2. Question types

| id | Label in the app | Prompt shows | Options (4, A–D) | Needs |
|---|---|---|---|---|
| `nghia` | Chọn nghĩa đúng | hanzi (large) + 🔊 | Vietnamese meanings | — |
| `chuhan` | Chọn chữ Hán đúng | Vietnamese meaning + từ loại | hanzi | — |
| `pinyin` | Chọn pinyin đúng | hanzi (large), no 🔊 | pinyin | — |
| `nghe` | Nghe và chọn từ | a big `🔊 Nghe` button only (no text) | hanzi | a `zh-CN` voice on the device |
| `dientu` | Điền từ vào chỗ trống | the word's example sentence with the word replaced by `＿＿`; `Gợi ý` reveals the Vietnamese translation | hanzi | `example.zh` contains `hanzi` exactly (true for 4,543 of 4,545 words) |
| `hanviet` | Chọn âm Hán Việt | hanzi (large) | Hán Việt readings | `hanviet` not empty (true for 4,523 words) |

- A word that doesn't meet a type's "Needs" simply never gets that type.
- If the device has no Chinese voice, hide `nghe` in the type chips with a one-line note, reusing the existing "Máy chưa có giọng đọc tiếng Trung" hint.
- Each question picks one of the chosen types at random among those valid for that word.

### B3. Generating options (the important part)
Write the generator as a **pure module** (`docs/js/quizcore.js`, no DOM) so it can be unit-tested over all 4,545 words. Use a seeded random generator in tests.

**Hard rules — every question must satisfy all of these:**
- Exactly 4 options, all different as displayed, and **exactly one correct**.
- A wrong option is **never** a word that:
  - has the same `hanzi` (some hanzi appear twice in a level)
  - appears in the target's `accept` list (e.g. 包含 accepts 包括, so 包括 can't be a wrong option for "bao gồm"), or has the target's hanzi in its own `accept` list
  - shares a meaning with the target. Split `meaning` on `,` and `;`, trim, lowercase and drop text in parentheses; any equal segment counts as shared.
- **`nghia`:** option texts are the full `meaning` strings. If one is very long (> 40 characters), show it up to the first `;`. Never show two options with identical text.
- **`nghe`:** wrong options must not sound the same as the target when tones are ignored (toneless pinyin differs), or the listening question would be unfair. About 100 words per level have a toneless homophone.
- **`pinyin`:**
  - Build wrong options mainly from **tone variants** of the correct pinyin: change the tone of one or two syllables, e.g. ānjìng → ànjìng / ānjīng / ánjìng.
  - When there aren't enough sensible variants (neutral-tone syllables, very short words), fill up with pinyin of other words with the same syllable count.
  - A variant must never equal any pinyin in the target's `accept` list.
  - Tone marks go on the correct vowel (a/e first, then o in "ou", otherwise the last vowel). Reuse `docs/js/check.js` helpers if they exist.
- **`hanviet`:** wrong options are other words' Hán Việt readings with the same syllable count, preferring ones that share a syllable. Never equal to the target's reading.
- **Making wrong options believable** (soft preferences, in order):
  1. same level
  2. same `pos`
  3. same number of characters
  4. for `chuhan` / `nghe` / `dientu`, sharing a character with the target

  Fall back to lower levels only if the level can't supply 3 valid wrong options.
- Shuffle the option order. Store which key is correct; don't rely on position.

### B4. Screens

**Quiz setup** (after tapping `Trắc nghiệm 📝`):
- **Type chips**, all six on by default. The choice is remembered (`settings.quizTypes`). At least one must stay on.
- **Word toggle:** `Tất cả từ` / `Chỉ từ đã thuộc` (`settings.quizPool`, default `all`). With `Chỉ từ đã thuộc` and none learned yet, show a friendly line and disable the start buttons.
- **Set size:** 10 / 20 / 50 / Tất cả (default 20; reuse the setting style from flashcards).
- Buttons:
  - `Làm câu mới` (words not yet answered correctly)
  - `Làm lại câu sai` (with count)
  - `Làm lại từ đầu` (resets quiz progress for this level, after an in-app confirmation)
  - `← Quay lại`

**Question screen** (match the Luyện đề question screen's look):
- **Header:** `HSK N · Trắc nghiệm` and `Câu x / y`; the type label under it.
- **Options:** four large tappable cards, A–D.
- **After tapping an option:**
  - the chosen option turns red if wrong, and the correct one turns green
  - below the options, show the word's full card: hanzi + 🔊, pinyin, Hán Việt, từ loại, nghĩa, example sentence + 🔊, its pinyin and Vietnamese translation (reuse the flashcard card-back markup in a compact form)
  - then `Tiếp`
- **`nghe`:** the first question needs a tap on `🔊 Nghe` (iOS). After that, the `Tiếp` tap may auto-play the next listening question. `🔁 Nghe lại` is always available.
- **`Thêm vào ôn tập`:** shown only when the answer was wrong **and** the word is currently learned in a flashcard direction. It sets the word back to not learned in both `zv` and `vz`, so it returns to normal flashcard study. Confirm with a small toast "Đã thêm vào ôn tập".

**End of set:**
- "Hoàn thành!", correct/total, and a short list of the words answered wrong (hanzi · pinyin · nghĩa).
- Buttons `Làm tiếp` / `Về cấp độ`.

**Nothing left:** "Bạn đã làm đúng hết từ của HSK N!", with `Làm lại câu sai` (if any) / `Làm lại từ đầu`.

### B5. Progress and storage (`docs/js/storage.js`)
- New key `hskfc.v1.quiz` → `{ "<word id>": { "ok": 1|0, "wrong": n } }`. This is **per word**, not per type.
- **Correct:** `ok: 1`, so the word leaves `Làm câu mới`.
- **Wrong:** `ok: 0, wrong + 1`, so the word appears in `Làm lại câu sai` until answered correctly.
- **Level screen and setup counts** use only that level's ids.
- **Backup / restore:** include it under `_quiz`, the same pattern as `_bank`; leave it out while empty. Old backups without `_quiz` still import, and leave the device's quiz progress alone.
- **Settings:** `quizTypes` (array of type ids) and `quizPool` (`all` | `learned`).

### B6. Service worker
Add the new module(s) to the app shell and bump the version.

### B7. Tests
- **Generator unit test** (Node), over all 4,545 words × every valid type, with fixed seeds:
  - 4 distinct options and exactly one correct
  - none of the excluded wrong options (same hanzi, accept list, shared meaning, toneless homophone for `nghe`)
  - pinyin variants differ from every accepted pinyin
  - Report how often the fallback to lower levels was needed.
- **Storage tests:** quiz progress, reset per level, backup/restore with and without `_quiz`.
- **Playwright at 390×844:**
  - level → Trắc nghiệm → setup
  - toggle types and pool; size
  - answer right and wrong; the card shows after answering
  - a correct word leaves `Làm câu mới`; a wrong one appears in `Làm lại câu sai`
  - `Thêm vào ôn tập` makes a learned word come back in flashcards
  - reset; offline after first load
  - `nghe` hidden when no zh voice (mock `speechSynthesis.getVoices`)
- **All existing tests** (`bash scripts/run_tests.sh`, including Luyện đề and the plaintext guard) still pass. If you refactor shared question UI out of `bank.js`, Luyện đề must behave exactly as before.

### B8. Done when
- All tests pass, and the change is published (on `main`, or merged — see the cloud-session rule in CLAUDE.md section 0).
- **Checkpoint for Quan**, phone test list:
  1. Reopen the app (close and open again) to get the new version.
  2. HSK 1 → `Trắc nghiệm 📝` → do a set of 10 with all types.
  3. Try `Chỉ từ đã thuộc`, and turn a few types off.
  4. Get one wrong on purpose, then `Làm lại câu sai`.
  5. On a word you'd learned in flashcards, get it wrong and tap `Thêm vào ôn tập` → it comes back in Trung → Việt.
  6. Listening type: tap 🔊 and hear the word.
- Log what was built in `PROGRESS.md`, including how often lower-level fallback was needed and any words that can't get some types.
