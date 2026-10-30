# Phase 8 — Luyện đề (question bank, self-paced)

A **question bank** built from HSK mock-test papers. Learners open it any time and do a few random questions at their own pace. **Not a formal test:** no timer, no sections to sit through, no pass mark.

Quan's decisions (2026-10-30). This spec replaces the earlier "formal mock test" version.
- Practice bank, not exams. Three tabs: **Nghe** (listening), **Đọc** (reading), **Sắp xếp câu** (sentence ordering).
- The questions live **inside the app**, but are **encrypted with a password Quan chooses**. Friends unlock once (magic link or password).
- The answer is shown right after each question. Questions answered correctly are hidden, like the flashcards; wrong ones come back.
- Listening audio is cut into **one clip per question** (one play + 🔁 replay button).
- First material: **HSK 4 only**. The design must still support any level; the app shows only levels that have a bank.

Read the whole spec before starting.

---

## 0. Hard rules

1. **No readable test content in git or on the site.** Everything under `docs/bank/` is encrypted. Plain question files, page images, audio and clips live only in `mock-tests/` (git-ignored). Automated tests use a made-up fixture (section 9).
2. **The password is never written into the repo, CLAUDE.md, PROGRESS.md, a spec, or a commit message.**
   - Build scripts read it from the environment variable **`BANK_PASSWORD`** first (set in the cloud environment — see section 11). If that's missing, they read `mock-tests/.bank-password` (local, ignored, and also in the private repo's `.gitignore`).
   - If neither exists, ask Quan.
   - The magic link contains the key, so treat it like the password: give it to Quan in the chat, don't write it to tracked files.
3. Add a test (section 9) that **fails if anything under `docs/bank/` is not encrypted** (readable JSON, MP3, WebP/PNG, or any CJK text). Run it before every commit that touches the bank.

---

## 1. Folders

```
Sample Test/                       # git-ignored: Quan's original files (423 MB), laptop only
mock-tests/                        # git-ignored in the public repo; it is its own PRIVATE repo (hsk-bank-private)
  .bank-password                   # local only, ignored even in the private repo
  materials/hsk4-book/             # compact copy of the book for the cloud: pages/ (JPG) + audio/ (MP3)
  work/<paper-id>/                 # extracted questions.json, clips/, review.html
scripts/bank/                      # build scripts — committed to the public repo (no content in them)
docs/bank/                         # ENCRYPTED output only — committed and published
```

- Paper id: `hsk{level}-{source}-{n}`, e.g. `hsk4-official-1`, `hsk4-book-a-3`.
- Record the exam version printed on the paper (HSK 2.0 or 3.0) in its source info.

### 1b. Current material: the HSK 4 book (scanned 2026-10-30)

**What it is**
- **Book:** 新HSK四级全真模拟测试题集 (BLCUP, 2012), **HSK 2.0 format**, **10 complete tests**.
- **Paper ids:** `hsk4-book-1` … `hsk4-book-10`. Title shown in the app: `Đề 1` … `Đề 10`.
- **The PDF is a scan:** images only, no text layer. Read pages visually. The compact page images are at `materials/hsk4-book/pages/p-NNN.jpg` (NNN = PDF page number, 150 dpi grayscale).
- **Audio:** one MP3 per test, ≈31 min each. Compact copies are at `materials/hsk4-book/audio/testNN.mp3` (mono 64 kbps). Quan's 128 kbps originals are in `Sample Test/` on the laptop. The audio has clear pauses (~1.5–2.5 s) between items.

**Page map** (PDF page = printed page + 15)
| Content | Printed pages | PDF pages |
|---|---|---|
| Test 1 … Test 10 (questions) | start at 2, 18, 34, 50, 66, 82, 98, 114, 130, 146; Test 10 ends at 163 | start at 17, 33, 49, 65, 81, 97, 113, 129, 145, 161; Test 10 ends at 178 |
| Listening script / answers / explanations (中英文), per test (script, answers, explanations) | Test 1: 164 / 170 / 171 … Test 10: 301 / 306 / 307 (the book's 目录 has every test's three page numbers) | add 15 |
| HSK 4 1200-word list by topic | 317–346 | 332+ (not needed) |
Verify the map against the 目录 page (PDF page 15) before extracting.

**Per test, what goes into the bank**
- **Nghe:** 45 questions (part 1: 10 `tf`; parts 2–3: 35 `choice`, with multi-question passages in part 3 as units).
- **Đọc:** 30 questions (part 1: 10 `wordbank` in two word lists; part 3: 20 `choice`).
- **Sắp xếp câu:** 20 questions (reading part 2: 10 `order-sentences`; writing part 1: 10 `order-words`).
- **Skip** writing part 2 (look at the picture, write a sentence).
- Expected total: **95 questions per test, about 950 in all.**

**Explanations**
- The book has an explanation for every answer (答案说明, in Chinese and English).
- Store the Chinese text as `explain_zh`, and fill `explain_vi` with a short Vietnamese version. Write those with a Haiku subagent like `example-writer` (cheap, in batches).
- Show `explain_vi` in the instant feedback, with `explain_zh` behind a small "Xem giải thích tiếng Trung" toggle.
- (Quan can switch this off at the first checkpoint.)

**Listening in HSK 4 is played once per item** (每题听一次), so the "one play only" step in section 4 normally has no repeat to remove. Still verify on test 1.

---

## 2. Question units and types

Some questions can't stand alone, so the bank stores **units**. A unit is one question, or a group that must be shown together:
- shared word bank
- a passage with 2–3 questions
- matching with shared options

A session always shows a whole unit.

| Tab | Type id | What the learner does | HSK 4 (2.0) part it usually comes from |
|---|---|---|---|
| Nghe | `tf` | Hear a clip, judge a printed statement ✓/✗ | Listening part 1 |
| Nghe | `choice` | Hear a clip, choose A/B/C/D | Listening parts 2–3 (a long passage with several questions is one unit) |
| Đọc | `wordbank` | Fill each blank from a shared word list A–F | Reading part 1 (one unit = one word list + its blanks) |
| Đọc | `choice` | Read a short text, choose A/B/C/D | Reading part 3 (a passage with 2 questions is one unit) |
| Sắp xếp câu | `order-sentences` | Put 3 sentences A/B/C in the right order | Reading part 2 (排列顺序) |
| Sắp xếp câu | `order-words` | Arrange words/phrases into one sentence | Writing part 1 (完成句子) |

- Other levels and HSK 3.0 papers may have other parts. Map them onto these types when they fit, add a type only if really needed, and **skip anything that isn't choose-or-order** (e.g. "write a sentence about the picture").
- Skip the worked examples (例如) at the start of each part.
- Both ordering types go in the third tab (Quan asked for it as a tab). Log this under `## Decisions`.

**Plain unit format** (`mock-tests/work/<paper-id>/questions.json`, never committed):
```json
{
  "paper": { "id": "hsk4-official-1", "level": 4, "examVersion": "HSK 2.0", "title": "Đề mẫu 1" },
  "units": [
    {
      "id": "hsk4-official-1-R1a",
      "skill": "doc", "type": "wordbank",
      "context": { "text": "", "pinyin": "", "image": null, "audio": null,
                   "sharedOptions": [ { "key": "A", "text": "禁止" } ] },
      "questions": [
        { "id": "hsk4-official-1-46", "prompt": "她每天都 ( ) 半个小时去运动。",
          "options": null, "answer": "E", "audio": null, "script": "" }
      ]
    }
  ]
}
```
- `options`: `[{ "key", "text"?, "image"? }]`, or `null` when the unit's `sharedOptions` apply.
- `tf`: options `✓` / `✗`.
- `order-sentences`: `options` = the 3 sentences with keys A/B/C, `answer` = e.g. `"BAC"`.
- `order-words`: `options` = the word/phrase tiles as printed, `answer` = the full correct sentence, `alsoAccept` = optional list of other correct sentences.
- `audio` (listening): path of that question's clip; a passage unit may have one clip in `context.audio` instead.
- `script`: the listening transcript for that question.
- **IDs must stay stable when a paper is rebuilt** — progress is stored against them.

---

## 3. Extracting a paper (main session model, not Haiku)

1. **Read the paper.**
   - Text PDF → PyMuPDF / pdfplumber.
   - Scanned → render pages to PNG at 150–200 dpi and read them visually.
2. Fill `questions.json`: answer key and listening script matched by question number, pictures (if any) cropped to WebP ≤ 600 px.
3. **Validate** with `scripts/bank/validate_paper.py`. It checks:
   - numbering is continuous and counts per part match the paper
   - every answer is valid (an option key, a permutation of A/B/C, or a sentence made of exactly the given tiles)
   - every referenced file exists
   - no unit is missing its shared options
4. **Write `work/<paper-id>/review.html`** (local only): every unit with its question, options, answer, script and an audio player for its clip. Flagged items go at the top in red.

---

## 4. Cutting the listening audio

Goal: one clip per question (or per passage, for multi-question passages), containing **one play** of the material. Exclude part announcements, instructions and examples.

1. **Find pauses:** `ffmpeg -af silencedetect` gives candidate boundaries.
2. **Find words:** transcribe with timestamps using **faster-whisper** (free, runs locally; a small or medium model is enough). Locate the question-number announcements (第X题, or just the numbers) and align the transcript with the listening script, to get each question's start and end.
3. **One play only:** HSK audio plays each item twice. Keep the first play and cut before the repeat (find the second occurrence of the script's opening words). If the two plays can't be separated confidently, keep both and note it.
4. **Export:** mono MP3 at about 48–64 kbps, with a little padding (≈0.3 s) at both ends.
5. **Auto-check each clip:**
   - re-transcribe the clip and compare it with that question's script; most key words must match
   - duration must be plausible
   - the number of clips must equal the number of questions in the part
   Anything failing is **flagged**.
6. **Never ship a clip you're unsure of.** A question with a bad clip is left out of the bank and listed in the report. Quan can say e.g. "question 7 starts 2 s late" — apply the fix and recheck.

Report to Quan: clips made / flagged / excluded for each part, and remind him that `review.html` is there for spot-checks.

---

## 5. Encryption and unlocking

Use the browser's built-in **Web Crypto API** (no library needed in the app). Build side: Python `cryptography`.

**Key**
- `key = PBKDF2-SHA256(password, salt, 310 000 iterations) → AES-256-GCM key`.
- `docs/bank/meta.json` (plain) holds: format version, salt, iteration count, the levels that have a bank, and a small encrypted "check" value used to tell a wrong password from a right one.
- Nothing else in `meta.json` — no titles, no counts by paper.

**Files**
- Each file in `docs/bank/` is `magic header (4 bytes) + 12-byte random IV + AES-GCM ciphertext`, extension `.bin`.
- One **index file per level** (`docs/bank/hsk4/index.bin`) holds all units of that level (text only).
- **Each audio clip and image is its own file**, named by a hash of its id + salt (`docs/bank/hsk4/m/3f9a….bin`), so names reveal nothing.
- `scripts/bank/build_bank.py`:
  - merges every `work/*/questions.json` for each level
  - drops excluded questions
  - encrypts everything
  - writes `docs/bank/`
  - deletes outputs that are no longer referenced
  - reports sizes
- It reads the password from `mock-tests/.bank-password`.

**Unlocking in the app**
- **Magic link:** `https://<site>/#k=<base64url raw key>`.
  - On load, the app imports the key, checks it against `meta.json`, stores it (IndexedDB, as a CryptoKey), then **removes the `#k=…` from the address bar** with `history.replaceState`.
  - The key after `#` is never sent to the server.
- **Password:** the Luyện đề screen shows one field, `Nhập mật khẩu`, plus `Mở khóa`. Wrong password → "Mật khẩu chưa đúng".
- **iPhone caveat:** an app added to the home screen may keep its own storage, separate from Safari. A friend who opened the magic link in Safari may have to type the password once inside the home-screen app. Say this in the how-to, and confirm the actual behaviour on Quan's iPhone at the checkpoint.
- **Changing the password later:** Quan tells you → rebuild everything with a new salt → new magic link. Old links and saved keys stop working, and the app asks for the new password ("Mật khẩu đã đổi, vui lòng nhập lại").

**Caching**
- The index is fetched and decrypted on unlock.
- Clips and images are fetched when first needed.
- The service worker caches `docs/bank/*` (cache `hskfc-bank`, kept across versions) so everything already seen works offline.
- In Cài đặt add `Tải toàn bộ đề về máy` (download all bank files for offline use, showing the size) and `Khóa lại` (forget the key on this device).

---

## 6. The app: Luyện đề

**Home screen.** New button below the five levels: `📝 Luyện đề`.

**Luyện đề screen**
- Locked → the unlock form (section 5).
- Unlocked → a list of levels that have a bank (HSK 4 for now), with progress, e.g. `HSK 4 · 312 câu · Đã làm đúng 40`.

**Level screen** — three tabs: `Nghe` · `Đọc` · `Sắp xếp câu`. Each tab shows:
- counts: `Còn N câu chưa làm đúng` / `Câu sai: M`
- `Làm câu mới` — random units containing questions not yet answered correctly
- `Làm lại câu sai` — only questions answered wrong at least once and not yet correct
- `Làm lại từ đầu` — resets this tab, with an in-app confirmation
- set size: 10 / 20 / Tất cả (counts questions; whole units are added until the size is reached)
- optional filter chips by question type, e.g. in Đọc: `Chọn từ` / `Đọc hiểu`. Default: all.

**Question screen (one unit at a time)**
- Context first: word list, passage, or audio player (`▶ Nghe` + `🔁 Nghe lại`; a tap starts audio, as iOS requires).
- Then each question of the unit, with options as large tappable cards (2–3 column grid for picture options).
- **Answer → instant feedback:** chosen option green or red, correct one green, and for listening the script appears under the question. Then `Tiếp`.
- A progress line at the top: `Câu 7 / 20`.
- A small `Nguồn: Đề mẫu 1` label (paper title only).

**Sắp xếp câu UX**
- Tiles in a pool. Tap a tile to add it to the answer line; tap a tile in the answer line to send it back. `Xóa` clears. `Kiểm tra` checks.
- **Correct** = matches `answer` or one of `alsoAccept` (ignore spaces and the final punctuation).
- **If wrong:** show the correct sentence and a small `Câu của mình cũng đúng` button. Word-order answers can have more than one valid form, so the learner may mark theirs as correct.

**End of set:** "Hoàn thành!", correct/total, buttons `Làm tiếp` / `Về danh sách`.

**Progress (localStorage)**
- Key `hskfc.v1.bank` → `{ "<question id>": { "ok": 1|0, "wrong": n } }`.
- Answered correctly → `ok: 1` and it won't appear in `Làm câu mới`. Wrong → `ok: 0, wrong + 1`, and it appears in `Làm lại câu sai`.
- Include `hskfc.v1.bank` in the existing progress backup and restore. Old backups without it must still import.

**Phone details**
- Large targets.
- Text size readable for Chinese (passages ≥ 18 px).
- Audio doesn't stop when tapping options.
- Works offline for anything already loaded.

---

## 7. Sharing with friends

After the first real bank is live, write Quan a short **Vietnamese message** he can paste into Zalo. It should contain:
- the app link
- the magic link
- what to do if asked for a password (ask Quan)
- the iPhone note from section 5

---

## 8. Adding more papers later

Quan drops a new paper in `mock-tests/source/` and says "add this paper". You then:
1. extract it and cut the audio
2. validate it and write its review page
3. rebuild the bank
4. run the plaintext check and the tests
5. publish

Friends get the new questions automatically, and their progress is kept because ids are stable.

---

## 9. Tests

- **Fixture:** a made-up bank in `scripts/fixtures/bank/` — a few invented units of every type, one generated image, two short generated tone clips — encrypted with the test password `test-password`. Never real content.
- **Plaintext guard:** fails if any file under `docs/bank/` lacks the magic header, parses as JSON, starts like MP3/WebP/PNG, or contains CJK text.
- **Playwright at 390×844:**
  - unlock with the password; wrong password message
  - unlock with the magic link, and the `#k=` is removed from the URL
  - all three tabs:
    - instant feedback on an answer
    - a correct answer disappears from `Làm câu mới`
    - a wrong answer appears in `Làm lại câu sai`
    - reset of a tab
    - ordering tiles add, remove, clear and check
    - `Câu của mình cũng đúng`
  - offline after first use
  - backup/restore includes bank progress
  - `Khóa lại`
- **Unit tests:** `validate_paper.py` with a broken paper; the crypto round-trip (Python encrypt → browser decrypt, using the fixture).
- All existing tests still pass.

---

## 10. Order of work and checkpoints

1. **Engine first, with the fixture only:** crypto, unlock, Luyện đề screens, three tabs, progress, tests → publish.
   - Tests serve the fixture from `scripts/fixtures/`; the live `docs/bank/` stays empty until a real bank exists.
   - With no `docs/bank/meta.json`, the Luyện đề screen just says "Chưa có đề — sắp có!".
2. **Check the inputs:**
   - The material is the HSK 4 book (section 1b), in `materials/hsk4-book/`.
   - The password comes from `BANK_PASSWORD` (section 0). If it isn't set, ask Quan.
   - Check the page map against the 目录.
3. **Build `hsk4-book-1` end-to-end:** extraction, explanations, audio clips, review page, encrypted bank, publish.
   **Checkpoint:** Quan
   - unlocks on his phone (magic link and password)
   - tries all three tabs
   - listens to some clips
   - spot-checks `review.html`
   Confirm the iPhone storage behaviour and fix the how-to.
4. **Remaining HSK 4 papers,** one at a time, with a short report each (questions added, clips flagged/excluded).
5. **Checkpoint:** the Zalo message for friends.

Log in `PROGRESS.md`: papers in the bank, question counts per tab, excluded questions and why — **never the password or the magic link**.

---

## 11. Running in a Claude Code cloud session (Quan's preferred way for Phase 8)

Quan has cloud-session credit and wants the heavy work done there.

**Two repositories in one cloud session**
- **`hsk-flashcards`** — public: the app, scripts, specs, and the encrypted `docs/bank/`.
- **`hsk-bank-private`** — private: the contents of `mock-tests/` (materials and work files). In the cloud, this checkout **plays the role of `mock-tests/`**. Build scripts take its path from the environment variable `BANK_PRIVATE_DIR`; if that isn't set, they use `../hsk-bank-private` if it exists, otherwise `mock-tests/`.

**Cloud environment** (Quan sets it up once at claude.ai/code)
- Network access **Custom**: the default list plus `huggingface.co`, `*.huggingface.co`, `*.hf.co` (needed to download the faster-whisper model). If the download is still blocked, ask Quan to switch the environment to **Full**.
- Environment variable `BANK_PASSWORD` — his chosen password. This environment is for him only.

**Rules in the cloud**
- At the start of every session (cloud or local), run `git pull` in both repositories.
- Commit work files (`questions.json`, clips, `review.html`) to `hsk-bank-private` as you go — the cloud machine is temporary, and anything not pushed is lost.
- Push the app, scripts and the encrypted `docs/bank/` to `hsk-flashcards` **only after all tests pass, including the plaintext guard**.
  - If you can push to `main`, do so; the live site updates from `main`.
  - If not, open a pull request and tell Quan to merge it.
- Never copy anything from `hsk-bank-private` into `hsk-flashcards` except through `build_bank.py`, which encrypts.
- `review.html` lives in the private repo. Quan reviews it on his laptop after `git pull` in `mock-tests/`, so tell him the path.
