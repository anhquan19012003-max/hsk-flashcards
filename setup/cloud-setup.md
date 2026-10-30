# Running Phase 8 in a Claude Code cloud session

**Why:** Phase 8 is heavy work: reading about 300 scanned pages and cutting 450 listening clips. Quan wants it to run on his cloud-session credit.

**The catch:** a cloud session only gets what's on GitHub, and the mock-test book must not go into the public repo. So the materials go into a second, **private** repo, `hsk-bank-private`, which is simply the `mock-tests/` folder pushed to GitHub. The cloud session opens both repos.

---

## Step 1 — on the laptop (local Claude Code, one time)

Open Claude Code in `App Build` and paste:

```
Read CLAUDE.md section 0, then do step 1 of setup/cloud-setup.md:
1. Run git status and make sure nothing from "Sample Test/" or "mock-tests/" is staged.
   Then commit and push the current changes (CLAUDE.md, specs/mock-tests.md, .gitignore,
   setup/cloud-setup.md) to main.
2. Turn mock-tests/ into its own git repo and push it to a NEW PRIVATE GitHub repo
   named hsk-bank-private (e.g. gh repo create hsk-bank-private --private --source mock-tests --push).
   Before pushing, check that mock-tests/.gitignore keeps .bank-password, source/,
   work/_preview/ and *.log out. After pushing, confirm the repo shows as Private on GitHub.
3. Report back. Don't start Phase 8 work locally.
```

The push is about 190 MB: the page images plus 10 audio files of about 15 MB each, all under GitHub's 100 MB file limit.

---

## Step 2 — let cloud sessions reach the private repo (one time)

Do **one** of these:
- **In Claude Code on the laptop (CLI):** run `/web-setup`. It gives cloud sessions access to every repo your GitHub login can reach, including private ones.
- **Or in the browser:** at claude.ai/code, connect GitHub and install the **Claude GitHub App** on `hsk-bank-private` (and on `hsk-flashcards`).

---

## Step 3 — create a cloud environment (one time, at claude.ai/code)

Add a new environment called **HSK bank**:
- **Network access → Custom:** tick "also include the default list", and add
  `huggingface.co`, `*.huggingface.co`, `*.hf.co`
  (the speech-recognition model used to cut the audio downloads from there). If Claude later reports the download is still blocked, change this to **Full**.
- **Environment variables:**
  ```
  BANK_PASSWORD=<the password you chose for the question bank>
  ```
  This environment is only yours. Don't share it.
- **Setup script** (optional; it saves a few minutes per session):
  ```
  pip install --break-system-packages faster-whisper cryptography pdfplumber pillow || true
  ```

---

## Step 4 — start the cloud session

At claude.ai/code:
- Choose **both** repos: `hsk-flashcards` and `hsk-bank-private`.
- Choose the **HSK bank** environment.
- Choose **Sonnet**.
- Paste:

```
Two repos are checked out: hsk-flashcards (public app) and hsk-bank-private (private;
it plays the role of mock-tests/). Read hsk-flashcards/CLAUDE.md section 0, then
specs/mock-tests.md completely (especially sections 0, 1b and 11).

Do Phase 8 in the spec's order: first the engine with the made-up fixture (step 1),
then build hsk4-book-1 end-to-end (steps 2–3), then stop at the checkpoint and report.
The bank password is in the BANK_PASSWORD environment variable — never print it or write it
into any file that gets committed.
Push work files to hsk-bank-private as you go. Push to hsk-flashcards only after all tests,
including the plaintext guard, pass. If you can't push to main, open a pull request and tell me.
Keep PROGRESS.md updated.
```

---

## During and after

- **Checkpoints:** the session stops after test 1 is in the bank.
  - Open the app on your phone, unlock, and try the three tabs.
  - On the laptop, run `git pull` inside `mock-tests/` and open `mock-tests/work/hsk4-book-1/review.html` to spot-check the clips.
  - Reply in the same cloud session (works from the Claude phone app too).
- **Pull request:** if the session opens one, merge it on GitHub. The live site updates a minute later.
- **Remaining tests:** say "continue" in the same session, or start a new cloud session with "Read CLAUDE.md section 0 and continue Phase 8".
- **Back on the laptop:** start with `git pull` in `App Build` and in `mock-tests/`. CLAUDE.md tells local sessions to do this anyway.
- **Credit:** cloud sessions share your account's usage limits. Check how your credit is being used in your Claude account settings.
