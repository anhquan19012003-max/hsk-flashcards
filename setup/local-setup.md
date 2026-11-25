# Running the project in normal (local) Claude Code sessions on Quan's PC

The cloud credit ended on 2026-11-05. From Phase 12 on, work happens in **Claude Code on Quan's Windows PC** ("nick-pc"). This page covers the one-time set-up and the daily routine.

## One-time set-up

### 1. Tools
Open Claude Code anywhere and paste:

```
Check that these are installed on this Windows PC and install whatever is missing
(winget for programs, pip for Python packages) — ask me before each install:
Git for Windows, GitHub CLI (gh), Python 3.11+, Node.js LTS, ffmpeg.
Python packages: pymupdf pillow cryptography openpyxl faster-whisper playwright,
then run: python -m playwright install chromium
Report the versions at the end.
```

### 2. GitHub login
This is needed for the private repo. In a terminal, run `gh auth login`, choose GitHub.com → HTTPS → "Login with a web browser", and approve in the browser.

### 3. Get both repos
Put them in `C:\Nick-Claude\` (next to `Chinnese Learning App`, which holds the books):

```
cd C:\Nick-Claude
gh repo clone anhquan19012003-max/hsk-flashcards
cd hsk-flashcards
gh repo clone anhquan19012003-max/hsk-bank-private mock-tests
git config core.hooksPath .githooks
```

The private repo is about 600 MB, so the second clone takes a few minutes.

### 4. Password file
Create `C:\Nick-Claude\hsk-flashcards\mock-tests\.bank-password` containing **only the bank password** (one line). If you've forgotten it, it's in claude.ai/code → environment **HSK bank** → `BANK_PASSWORD`. The file is git-ignored, so it never leaves the PC.

### 5. Check
Open Claude Code **in `C:\Nick-Claude\hsk-flashcards`** and paste:

```
Read CLAUDE.md section 0 and PROGRESS.md. This is a fresh local set-up on my Windows PC:
check that both repos are on main and up to date, the hooks path is set, mock-tests/.bank-password
exists (don't print it), and run bash scripts/run_tests.sh. Report what passed and anything missing.
```

Use **Sonnet** as the model (`/model`).

## Daily routine
- **Start** with "status". Claude Code pulls both repos and tells you where things stand.
- **Work one step or one test per session.** Local sessions use your normal plan limits, and reading scanned pages uses the most.
- **Stop** with "stop" / "dừng". It saves, updates `PROGRESS.md` and pushes.
- **No branches to merge.** Local sessions push straight to `main` after the tests pass. The live site updates a minute or two later.

## Where things are
| What | Where |
|---|---|
| App repo (public) | `C:\Nick-Claude\hsk-flashcards` |
| Private repo (bank work files) | `C:\Nick-Claude\hsk-flashcards\mock-tests` |
| Original books and audio (never in git) | `C:\Nick-Claude\Chinnese Learning App\HSK N sample test\` |
| Bank password | `mock-tests\.bank-password` (and the cloud environment "HSK bank") |
