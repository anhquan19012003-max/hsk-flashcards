#!/usr/bin/env bash
# Runs every test, ending with the plaintext guard. Usage: bash scripts/run_tests.sh
set -e
cd "$(dirname "$0")/.."
echo "== plaintext guard";            python3 scripts/bank/guard.py
echo "== bank: unit tests";           python3 scripts/test_bank_unit.py
echo "== bank: browser-side logic";   node scripts/test_bankjs.mjs
echo "== storage / check / strokes";  node scripts/test_storage.mjs; node scripts/test_check.mjs; node scripts/test_strokematch.mjs
echo "== app";                        python3 scripts/test_app.py
echo "== writing";                    python3 scripts/test_writing.py
echo "== bank: browser";              python3 scripts/test_bank.py
echo "== bank: download shortcut + Cài đặt"; python3 scripts/test_bank_download.py
echo "== bank: HSK 3 layouts, two levels, per-level download"; python3 scripts/test_bank_hsk3.py
echo "== quiz: generator over all 4,545 words"; node scripts/test_quizcore.mjs
echo "== quiz: screens"; python3 scripts/test_quiz.py
echo "== real bank smoke test (skipped without BANK_PASSWORD)"; python3 scripts/test_real_bank.py
echo "== plaintext guard (final)";    python3 scripts/bank/guard.py
echo "ALL TESTS PASSED"
