# HSK Flashcards — project brief

A free, static, phone-friendly flashcard web app for learning HSK 3.0 vocabulary (levels 1–5, 4,545 words), aimed at Vietnamese learners. The owner (Quan) shares the link with friends; each person's progress lives on their own phone. **All UI text is in Vietnamese.**

Read this file at the start of every session. Work phase by phase (see section 6). Do not skip the review step for generated content.

---

## 0. How to work with Quan (read first, every session)

Quan planned this project in a separate chat and doesn't want to go back to it — **you are his main point of contact.** He uses Claude Code but isn't a full-time developer, and he is a beginner Chinese learner.

**Where things stand.** Phases 0–5, 7 and 8 are done (Phase 8 = Luyện đề: engine live, all 10 HSK 4 papers in the encrypted bank; Quan's phone test is still open), see PROGRESS.md: all 5 levels have Hán Việt and example sentences, and the app is live on GitHub Pages (repo `hsk-flashcards`). New features are added as numbered phases (section 6), each with a full spec in `specs/`. Read the spec of the phase you're working on before starting it.

**Session start.** Run `git pull` (also in `mock-tests/`, which is the private repo `hsk-bank-private`; in a cloud session that repo is checked out next to this one — see `specs/mock-tests.md` section 11). Then read `PROGRESS.md` (if it doesn't exist yet, create it and fill `## Done` from `git log`). In 3–5 lines tell Quan: which phase we're in, what was done last time, and the next step. Then wait for him to say go — unless he already gave an instruction.

**Keep `PROGRESS.md` up to date** after every step and every decision:
- `## Status` — current phase and step
- `## Done` — one line per finished step, with date
- `## Waiting on Quan` — anything you need from him (a phone test, a review, a decision)
- `## Decisions` — every choice he made that isn't in this file or a spec, with date
- `## Known issues` — anything left unfinished or flagged
This file is how a fresh session (or a different model) picks up exactly where the last one stopped.

**Run continuously; stop only at checkpoints.** Work through a phase without asking permission between steps. Stop and report only:
1. at the checkpoint named at the end of each phase or spec (usually: Quan tests on his phone)
2. when something needs his accounts or a decision only he can make (GitHub login, changing the design, deleting work)
3. at a real blocker you can't solve after two genuine attempts

**Checkpoint report format** (short, plain language):
- ✅ **Done:** 2–4 bullets
- 👀 **Please check:** exactly what to open or tap, and what "good" looks like
- ❓ **Need from you:** questions as numbered options, with your recommendation marked
- ▶️ **Next:** what you'll do when he says "continue"

**Answering questions.** If Quan asks how something works or why you chose it, explain briefly with a concrete example. If he asks for a change, say what it affects. If it changes something in this file or a spec, update that file and log it under `## Decisions`. Never quietly drop a feature that's described here or in a spec.

**Things Quan may say, and what to do:**
| He says | You do |
|---|---|
| "status" / "where are we" | Summarise `PROGRESS.md` in a few lines |
| "continue" / "tiếp" | Carry on from `## Status` |
| "stop" / "dừng" | Finish the current step, save, update `PROGRESS.md`, stop |
| "I reviewed HSK N" | Run `import_review.py N`, validate, rebuild, publish, report what changed |
| "change X in the app" | Make the change, test it at phone size, publish, tell him what to check |
| "new feature: …" | Write a short spec in `specs/`, add a phase in section 6, confirm the plan with him, then build |

**Publishing.** Every app or content change ends with: run the tests → bump the service-worker version → commit → push, so the live site updates. Tell Quan to reopen the app on his phone to get the new version.

**Usage.** Don't read big data files into the conversation (use scripts and summaries). Use the Haiku subagent for bulk content as in 3e. If a session gets long, finish the step, save, and suggest a fresh session.

**Language.** Reply in the language Quan writes in (English or Vietnamese). App UI and generated content are always Vietnamese.

---

## 1. Source data

`source/vocab.xlsx` — only the `Data_HSK1` … `Data_HSK5` sheets matter (the `Từ vựng HSK*` sheets are Excel practice formulas; `Huong_Dan` documents the original answer-checking rules).

Columns in each `Data_HSK*` sheet (header in row 1, data from row 2):

| Col | Header | Notes |
|---|---|---|
| A | STT | row number within the level — use for stable IDs |
| B | Chữ Hán | simplified; a few contain parentheses, e.g. `有(一)些`, `有(一)点儿` |
| C | Pinyin | tone marks, no spaces between syllables (e.g. `àihào`) |
| D | Từ loại | filled for HSK1–3; **empty for HSK5, almost all empty for HSK4** |
| E | Nghĩa tiếng Việt | meaning shown on cards |
| F | Đáp án chấp nhận | accepted answers separated by `;` (hanzi, pinyin with/without tones, synonyms) |
| G, H | formulas | ignore |

Counts: HSK1 500 · HSK2 772 · HSK3 973 · HSK4 1000 · HSK5 1300.

Known data quirks (verified):
- **The same hanzi can appear twice in one level** with different pinyin/meaning (e.g. HSK2 `长` cháng/zhǎng, `得`, `倒`; HSK1 `地`, `干`, `还`). Treat them as separate cards. **Never key anything by hanzi — use the ID.**
- 828 words appear in more than one level. Keep each level's list exactly as the file has it; levels are independent.
- Ignore the empty pre-formatted rows at the bottom of each sheet (stop when column B is empty).

---

## 2. Data model

One JSON file per level: `docs/data/hsk{N}.json`

```json
{
  "level": 4,
  "count": 1000,
  "words": [
    {
      "id": "4-0001",
      "hanzi": "阿姨",
      "pinyin": "āyí",
      "pos": "danh từ",
      "meaning": "cô, dì, thím",
      "accept": ["阿姨", "āyí", "ayi"],
      "hanviet": "a di",
      "example": {
        "zh": "阿姨每天早上都去公园跑步。",
        "pinyin": "Āyí měitiān zǎoshang dōu qù gōngyuán pǎobù.",
        "vi": "Dì sáng nào cũng ra công viên chạy bộ."
      }
    }
  ]
}
```

- `id` = `{level}-{STT zero-padded to 4}`. Stable forever; progress is stored against it.
- `accept` comes from column F (split on `;`, trimmed), always including `hanzi` and `pinyin`.
- `pos`: copy column D. For HSK4–5 where it is empty, fill it during enrichment, using the same Vietnamese labels as HSK1–3 (`danh từ`, `động từ`, `tính từ`, `phó từ`, `lượng từ`, `giới từ`, `liên từ`, `trợ từ`, `đại từ`, `số từ`, `thán từ`…, comma-separated if several).
- Working files (not deployed) live in `data/` — see layout below. Keep any validator flags there, not in the deployed JSON.

---

## 3. Content to generate

### 3a. Hán Việt (`hanviet`)
Lowercase, one syllable per character, separated by spaces: `安排` → `an bài`, `银行` → `ngân hàng`.

Method — do **not** write these from memory:
1. Build a per-character table from **Unicode Unihan `kVietnamese`** (`Unihan_Readings.txt` in Unihan.zip from unicode.org). `kVietnamese` is mostly keyed on traditional characters, so map simplified → traditional first (Unihan `kTraditionalVariant`, or OpenCC `s2t`) and look up both forms.
2. Characters with a single reading → assemble automatically.
3. Characters with several readings (e.g. 行 hành/hàng, 长 trường/trưởng, 乐 lạc/nhạc, 好 hảo/hiếu, 重 trọng/trùng, 调 điều/điệu, 为 vi/vị) → choose the reading that matches the word's pinyin/meaning; mark `hanviet_check: true` in the working file when unsure.
4. Characters with no reading found → mark for review, never guess silently.
5. Parentheses stay: `有(一)些` → `hữu (nhất) ta`.
6. Particles/interjections (吧, 啊, 呢, 吗…) still get their reading (ba, a, ni, ma); it's fine that these are less meaningful.

**As built (Phase 1 finding):** Unihan `kVietnamese` turned out to be unreliable for this vocabulary — it mixes Nôm readings in (跟 "ngấn", 为 "vay", 好 "háo"), often lists them first, and has no entry at all for ~300 common characters (爱, 问, 面…). So the sources are, in order: English Wiktionary `{{vi-readings}}` (`scripts/fetch_wiktionary.py` → `data/wiktionary_hanviet.json`; explicit `hanviet=`/`hv=` lists are trusted, the older `reading=` lists mix in Nôm), then Unihan as a last resort (always flagged). `scripts/hanviet.py` only ever *selects* among sourced candidates: `POLYPHONE` (by the word's pinyin), `CHOICE` / `LOWCONF` in `scripts/hanviet_choices.py` (LOWCONF picks are flagged). Characters with no source reading stay `?` and are flagged — they are the first thing Quan should fill in the review files.

### 3b. Example sentence (`example`)
**Exactly one short sentence per word.** Written by the `example-writer` subagent (Haiku — see 3e), following these rules:
- Contains the target word exactly as written (for separable verbs like 洗澡 / 见面 a split form such as 洗了个澡 is allowed but flag it). Use the sense given in `meaning` (the first meaning if several).
- **Only uses vocabulary at the card's level or lower.** HSK1 sentences use only HSK1 words, and so on.
- Keep it short — the point is to show the word in use, not to tell a story. Length limit (Chinese characters, excluding punctuation): HSK1–2 ≤ 10, HSK3–5 ≤ 15. Natural, everyday, neutral topics; no names of real people; no politics.
- For measure words, particles and conjunctions, the sentence must show the typical pattern (e.g. 一**张**纸, 你吃饭了**吗**？).
- `pinyin`: tone marks, words separated by spaces, first letter capitalised, punctuation kept.
- `vi`: natural Vietnamese, not word-for-word.
- Each sentence should be different; don't reuse a template across many words.
- **Quan's Phase 3 decision:** Haiku stays. Characters outside the card's level and duplicate sentences are *acceptable* — the validator still reports them, but they are not retried or fixed. Hán Việt does not need to be 100% correct. Only structural flags (target word missing, too long, pinyin/character count mismatch, empty `vi`) are retried once.

### 3c. Validation script (`scripts/validate.py`) — run after every batch
Flag (don't auto-fix):
- example doesn't contain the target word
- any character in the example not found in the words of levels ≤ N (character-level check against all hanzi in those levels; allow common punctuation and digits)
- over the length limit
- pinyin syllable count ≠ Chinese character count (ignore punctuation; 儿 may merge)
- missing tone marks, empty `vi`, empty `hanviet`, `hanviet` syllable count ≠ character count
- duplicate example sentences
Print a summary per level and write flags to the working file.

### 3d. Human review loop
- `scripts/export_review.py N` → `review/hsk{N}_review.xlsx`: one row per word with id, hanzi, pinyin, meaning, pos, hanviet, example zh/pinyin/vi, validator flags, `hanviet_check`, plus an empty "Ghi chú / sửa" column. Flagged rows highlighted, frozen header, filters on.
- Quan edits cells directly in the xlsx.
- `scripts/import_review.py N` applies the edits back to `data/enriched/hsk{N}.json`, then re-run validate, then rebuild `docs/data/hsk{N}.json`.

### 3e. Batching and model use (save usage)
The bulk writing is done by a cheaper model. The main session only coordinates and checks.

- **`example-writer` subagent** (`.claude/agents/example-writer.md`, `model: haiku`) writes `example` (zh / pinyin / vi) — and `pos` for HSK4–5 — for one batch at a time.
- **Main session** (whatever model Quan runs Claude Code with):
  1. Uses a script to cut the next batch of **50 words** to `data/batches/hsk{N}_{from}-{to}.in.json` (fields: id, hanzi, pinyin, pos, meaning, level).
  2. Delegates that file to `example-writer`, which writes `…out.json` next to it.
  3. Merges the output into `data/enriched/hsk{N}.json` and runs `scripts/validate.py`.
  4. Sends only the flagged words back to `example-writer` **once** for a retry.
  5. Fixes whatever is still flagged itself (should be a small number), or leaves it flagged for Quan's review.
  6. Does not rewrite Haiku's sentences that passed validation.
- Several batches can be delegated in parallel. Every batch is saved to disk, so a session can stop and resume anywhere (skip batches whose `.out.json` already exists).
- The Hán Việt work (3a) is mostly a script; polyphonic choices are few enough for the main session.
- Keep the rules in 3b and the subagent file in sync — if Quan changes a rule after the pilot, update both.
- Order: HSK1 → HSK5.

---

## 4. The app

### Tech
- Plain HTML + CSS + vanilla JavaScript (ES modules). **No framework, no build step.** Everything deployable lives in `docs/`.
- Mobile-first (design for 360–430 px wide; still fine on desktop). Large tap targets (≥ 44 px), large hanzi (≥ 64 px on the card front), system fonts with a CJK fallback (`"PingFang SC", "Noto Sans SC", "Microsoft YaHei", sans-serif`).
- Installable PWA: `manifest.webmanifest` (name "Thẻ từ vựng HSK", icons 192/512, `display: standalone`) + a service worker that caches the app shell and every level file it has loaded, so it works offline. Bump the cache version on every deploy.
- Never use `alert` / `confirm` / `prompt` — use in-app dialogs.

### Screens and flow
**1. Trang chủ (Home)** — title "Thẻ từ vựng HSK". Five large buttons, HSK 1 … HSK 5, each showing word count and progress, e.g. `HSK 4 · 1000 từ · Đã thuộc 120`. Gear icon → Cài đặt.

**2. Màn hình cấp độ (Level screen)** — after choosing a level; everything below only uses that level's words:
- `Trung → Việt` (shows remaining count)
- `Việt → Trung (gõ đáp án)` (shows remaining count)
- `Ôn lại từ đã thuộc` (choose direction; shows learned count)
- `Học lại từ đầu` — resets this level's progress after an in-app confirmation
- `← Chọn cấp độ khác`

**3. Học (Study session)**
- Deck = **random shuffle of the words not yet learned in this direction**, a new shuffle every session. Session size from settings (10 / 20 / 50 / Tất cả, default 20). Header shows `7 / 20`.
- **Trung → Việt card**: front = hanzi (large) + 🔊. Tap card or `Lật thẻ` → back.
- **Việt → Trung card**: front = Vietnamese meaning + từ loại. A text box (`autocapitalize="off" autocorrect="off" spellcheck="false"`), button `Kiểm tra`, and a `Lật thẻ` button for when they can't answer. After checking, show ✅ Đúng / ❌ Chưa đúng with what they typed, then the back.
- **Back of every card**: hanzi + 🔊, pinyin, Hán Việt, từ loại, nghĩa; then the example sentence (zh, with the target word highlighted) + 🔊, its pinyin, its Vietnamese translation.
- Then two buttons: `Đã thuộc ✓` and `Chưa thuộc ✗`.
  - `Đã thuộc` → saved as learned for this direction; won't appear in normal study again.
  - `Chưa thuộc` → card goes back into this session's deck 5–8 cards later (or at the end if fewer remain).
- **End of session**: "Hoàn thành!" with counts (đã thuộc / chưa thuộc), buttons `Học tiếp` and `Về trang chủ`.
- When everything in a direction is learned: "Bạn đã thuộc hết HSK N (chiều …)!" with `Ôn lại` / `Học lại từ đầu`.

**4. Ôn lại (Review learned words)** — random shuffle of learned words. Same card, but buttons `Vẫn nhớ` (stays learned) / `Quên rồi` (moves back to not learned).

**5. Cài đặt (Settings)** — session size; reading speed (chậm / bình thường); `Sao lưu tiến độ` (download a JSON file) and `Khôi phục tiến độ` (upload that file); `Cách cài lên điện thoại` (short instructions: iPhone → Safari → Chia sẻ → Thêm vào MH chính; Android → Chrome → menu ⋮ → Cài đặt ứng dụng / Thêm vào màn hình chính).

### Answer checking (Việt → Trung)
Same rules as the original Excel file:
- Accept any entry in `accept` (hanzi or pinyin).
- Ignore case, spaces, apostrophes, `·`, `-`, parentheses.
- `ü` may be typed as `ü`, `v` or `u`.
- Pinyin **with** tone marks must have the correct tones; pinyin **without** tone marks only checks the letters.
- Also accept tone numbers (`ai4hao4`) — convert to tone marks before comparing.

### Progress (localStorage)
- Key `hskfc.v1.progress` → `{ "4-0001": { "zv": 1, "vz": 0, "wr": 0 } }` where `zv` = learned Trung → Việt, `vz` = learned Việt → Trung, `wr` = learned in Luyện viết (added in Phase 7; entries without it are valid). **Each direction is tracked separately.**
- Key `hskfc.v1.settings` for settings.
- Wrap every read/write in try/catch; if storage is unavailable, the app still works without saving.
- Backup/restore uses the same JSON shape.

### Audio
- Use the browser's built-in `speechSynthesis` with `lang = "zh-CN"`; choose a `zh-CN` voice from `getVoices()` (wait for `voiceschanged`). Rate ≈ 0.9 for words, ≈ 0.8 for sentences ("chậm" setting lowers both).
- Only start speech from a tap (iOS requirement). Cancel any current speech before speaking.
- Speak the hanzi, never the pinyin.
- If there's no Chinese voice: show a small message "Máy chưa có giọng đọc tiếng Trung" with a hint (Android: Cài đặt → Chuyển văn bản thành giọng nói → tải tiếng Trung).

---

## 5. Folder layout

The project root is the folder this CLAUDE.md is in (on Quan's laptop: `App Build`).

```
App Build/
  CLAUDE.md
  PROGRESS.md                  # live status — see section 0
  specs/                       # one spec per feature phase (e.g. writing-practice.md)
  Sample Test/                 # GIT-IGNORED: Quan's original mock-test book + audio (423 MB), laptop only
  mock-tests/                  # GIT-IGNORED here; it is the PRIVATE repo hsk-bank-private (materials, work files) — Phase 8
  .claude/agents/example-writer.md   # Haiku subagent for example sentences (copied from setup/ in Phase 0)
  setup/example-writer.md            # original copy of the subagent file
  source/vocab.xlsx            # original file, never modified
  data/batches/                # 50-word in/out files for the subagent
  scripts/                     # Python: extract, hanviet, validate, export_review, import_review, build
  data/raw/hsk{N}.json         # straight from Excel
  data/enriched/hsk{N}.json    # + hanviet, pos, example, flags
  review/hsk{N}_review.xlsx    # for Quan to review
  docs/                        # the deployed app (GitHub Pages serves this folder)
    index.html  styles.css  app.js  sw.js  manifest.webmanifest
    icons/
    data/hsk{N}.json           # built from data/enriched, no flags
```

---

## 6. Phases

**Phase 0 — Setup (first session only)**
If `.claude/agents/example-writer.md` does not exist, create the folder and copy `setup/example-writer.md` there unchanged, then tell Quan to restart Claude Code (or run `/agents`) so the subagent is picked up. Initialise a git repo with a sensible `.gitignore` (Python caches, OS files).
✅ Done when: `/agents` lists `example-writer` with model haiku.

**Phase 1 — Data foundation**
`scripts/extract.py` → `data/raw/hsk1..5.json`; assert counts (500/772/973/1000/1300) and unique IDs. Build the Hán Việt table and fill `hanviet` for all 4,545 words; export the review files for the items flagged `hanviet_check` or with no reading.
✅ Done when: all raw files exist, every word has `hanviet` or a review flag.

**Phase 2 — App, first version**
Build the full app using the HSK1 data (example sentences may still be empty — hide that section when missing). Test in a mobile-sized browser window (Playwright, 390×844) and on a real phone.
✅ Done when: choose level → both modes → mark learned → reload → learned words don't come back; review mode and reset work; audio works on a phone.

**Phase 3 — Example sentences, HSK1 pilot**
Generate HSK1 examples with the Haiku subagent + validate + export review. Report how many words were flagged on the first pass vs after retry. **Stop and wait for Quan's review** before continuing — this is also where we decide whether Haiku's quality is good enough (if not, switch the subagent to `model: sonnet`). Adjust the rules in 3b and the subagent file based on his feedback.

**Phase 4 — Example sentences, HSK2–5**
Same loop, level by level (fill `pos` for HSK4–5 at the same time).

**Phase 5 — Deploy**
GitHub repo, GitHub Pages from `main` / `docs`. PWA install tested on iPhone (Safari) and Android (Chrome). Offline test: open once, turn on airplane mode, still works.

**Phase 6 — Optional extras (only if asked)**
Spaced-repetition mode, search/browse list, dark mode, pre-recorded audio.

**Phase 7 — Luyện viết (writing practice)** — *done 2026-10-30*
Full spec: **`specs/writing-practice.md`** — read it completely before starting. Uses the free Hanzi Writer library and its stroke data (no paid API), vendored into `docs/vendor/` and `docs/hanzi/`. Adds a `Luyện viết` mode on the level screen and a `✍️ Viết` button on the back of every card.
**Checkpoint:** Quan tests drawing on his phone (list in the spec, section 7).

**Phase 8 — Luyện đề (self-paced question bank)** — *done 2026-10-30*
Full spec: **`specs/mock-tests.md`** — read it completely before starting. Not a formal test: a bank of questions from HSK mock-test papers (HSK 4 first), done at your own pace in three tabs — **Nghe**, **Đọc**, **Sắp xếp câu** — with instant feedback, and correct answers hidden like the flashcards. Listening audio is cut into one clip per question. The bank lives inside the app but **encrypted with a password Quan chooses**; friends unlock with a magic link or the password.
**Hard rules:** no readable test content in git or on the site (`mock-tests/` is git-ignored, `docs/bank/` holds only encrypted files); never write the password or magic link into any tracked file.
**Material:** the HSK 4 book with 10 tests (scanned PDF + 10 MP3s) in `Sample Test/` (git-ignored, laptop only); a compact copy for the cloud is in `mock-tests/materials/hsk4-book/` (spec section 1b).
**Where:** Quan wants Phase 8 run in a **Claude Code cloud session** with two repos — this one and the private `hsk-bank-private` (spec section 11; setup steps in `setup/cloud-setup.md`).
**Checkpoints:** after the engine is live (fixture only), after the first real paper (Quan tests on his phone), and when the HSK 4 papers are done.

**Later ideas (not started — ask Quan before building)**
- Vocab quiz generated from the app's own data (meaning ↔ hanzi, pinyin, fill-in-the-blank from the example, listen-and-choose) — could reuse the Phase 8 question screens.
- Pronunciation practice: free browser speech recognition only works in a browser tab (not from the home-screen app on iPhone); real tone scoring would need a paid service such as Azure pronunciation assessment plus a small server.

---

## 7. Working rules
- Never modify `source/vocab.xlsx`.
- Never commit or publish readable mock-test content (anything under `Sample Test/` or `mock-tests/`, or real questions, pictures or audio outside the encrypted `docs/bank/`), and never write the bank password or magic link into a tracked file.
- Never key data by hanzi; always by `id`.
- Never overwrite Quan's review edits — `import_review` is the only path that changes reviewed rows.
- Keep generated content and UI text in Vietnamese; code and comments in English.
- After each phase, report in the checkpoint format from section 0 and update `PROGRESS.md`.
