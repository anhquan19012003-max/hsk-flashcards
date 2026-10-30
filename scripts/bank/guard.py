"""Plaintext guard (specs/mock-tests.md sections 0 and 9). Standard library only.

Fails (exit 1) if readable test content could reach the public site:
  * a file under docs/bank/ that is not meta.json or a .bin file with the encrypted-file magic header
  * an encrypted-looking file that parses as JSON, starts like MP3/WebP/PNG/JPEG/PDF/WAV/OGG, or holds CJK text
  * a meta.json with anything besides the allowed keys
  * a tracked path under mock-tests/ or Sample Test/ (when run inside a git checkout)

  python scripts/bank/guard.py [--bank DIR]
"""
import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

MAGIC = b"HSKB"
META_KEYS = {"v", "salt", "iter", "levels", "check"}
# 4+ CJK characters in a row (random bytes rarely produce even one valid sequence, let alone four)
CJK_RUN = re.compile(r"[㐀-䶿一-鿿豈-﫿　-〿＀-￯]{4,}")
SIGNATURES = [
    (b"ID3", "MP3"), (b"\xff\xfb", "MP3"), (b"\xff\xf3", "MP3"), (b"\xff\xf2", "MP3"), (b"\xff\xe3", "MP3"),
    (b"RIFF", "WebP/WAV"), (b"\x89PNG", "PNG"), (b"\xff\xd8\xff", "JPEG"), (b"%PDF", "PDF"), (b"OggS", "Ogg"),
    (b"GIF8", "GIF"), (b"fLaC", "FLAC"), (b"\x00\x00\x00\x1c", "MP4"), (b"\x00\x00\x00\x20", "MP4"),
]
ROOT = Path(__file__).resolve().parent.parent.parent


def entropy(data: bytes) -> float:
    n = len(data)
    return -sum(c / n * math.log2(c / n) for c in Counter(data).values())


def has_cjk(data: bytes) -> bool:
    # UTF-8 only: decoding random bytes as UTF-16 or GB18030 produces CJK constantly, so those would false-alarm on ciphertext
    return bool(CJK_RUN.search(data.decode("utf-8", errors="replace")))


def check_bank(bank: Path):
    problems = []
    if not bank.exists():
        return problems  # no bank yet is fine
    for p in sorted(bank.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(bank).as_posix()
        data = p.read_bytes()
        if rel == "meta.json":
            try:
                meta = json.loads(data.decode("utf-8"))
            except Exception:
                problems.append(f"{rel}: not valid JSON")
                continue
            extra = set(meta) - META_KEYS if isinstance(meta, dict) else {"(not an object)"}
            if extra:
                problems.append(f"{rel}: unexpected keys {sorted(extra)}")
            if has_cjk(data):
                problems.append(f"{rel}: contains CJK text")
            continue
        if not rel.endswith(".bin"):
            problems.append(f"{rel}: only .bin files and meta.json are allowed in docs/bank/")
            continue
        if data[:4] != MAGIC:
            problems.append(f"{rel}: missing encrypted-file magic header")
        if len(data) < 4 + 12 + 16:
            problems.append(f"{rel}: too short to be an encrypted file")
        for sig, name in SIGNATURES:
            if data.startswith(sig):
                problems.append(f"{rel}: starts like {name}")
        try:
            json.loads(data.decode("utf-8"))
            problems.append(f"{rel}: parses as JSON")
        except Exception:
            pass
        if has_cjk(data):
            problems.append(f"{rel}: contains CJK text")
        if len(data) >= 4096 and entropy(data) < 7.9:
            problems.append(f"{rel}: entropy {entropy(data):.2f} is too low for ciphertext")
    return problems


def check_tracked(root: Path):
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
    except Exception:
        return []  # not a git checkout
    return [f"{path}: private material must never be tracked here" for path in out.splitlines()
            if path.startswith(("mock-tests/", "Sample Test/"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", type=Path, default=ROOT / "docs" / "bank")
    ap.add_argument("--no-git", action="store_true")
    args = ap.parse_args()
    problems = check_bank(args.bank) + ([] if args.no_git else check_tracked(ROOT))
    n = sum(1 for p in args.bank.rglob("*") if p.is_file()) if args.bank.exists() else 0
    if problems:
        print(f"PLAINTEXT GUARD FAILED ({len(problems)} problem(s)):")
        for line in problems:
            print("  -", line)
        sys.exit(1)
    print(f"plaintext guard OK ({n} file(s) checked in {args.bank})")


if __name__ == "__main__":
    main()
