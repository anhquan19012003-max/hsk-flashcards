"""Copy the stroke-order data for every Han character used in docs/data/hsk1..5.json to docs/hanzi/{char}.json.

Source: npm package `hanzi-writer-data` (pinned below; derived from Make Me a Hanzi, Arphic Public License).
Only characters that docs/hanzi/ does not have yet need the source; if any are missing the package is downloaded
once with `npm pack` into data/cache/ (git-ignored). Files for characters no longer in the vocabulary are removed.
Called from scripts/build.py, and can be run alone: python scripts/build_hanzi_data.py
"""
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PACKAGE = "hanzi-writer-data@2.0.1"
OUT = ROOT / "docs" / "hanzi"
CACHE = ROOT / "data" / "cache"
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿\U00020000-\U0002fa1f]")


def vocabulary_chars():
    chars = set()
    for path in sorted((ROOT / "docs" / "data").glob("hsk*.json")):
        for w in json.loads(path.read_text(encoding="utf-8"))["words"]:
            chars.update(HAN.findall(w["hanzi"]))
    return chars


def source_dir():
    """Directory holding {char}.json files from the hanzi-writer-data package (downloaded once)."""
    pkg = CACHE / "package"
    if not pkg.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"downloading {DATA_PACKAGE} (one time, ~50 MB) ...")
        subprocess.run(["npm", "pack", DATA_PACKAGE, "--silent"], cwd=CACHE, check=True, shell=sys.platform == "win32")
        tarball = next(CACHE.glob("hanzi-writer-data-*.tgz"))
        with tarfile.open(tarball) as tar:
            tar.extractall(CACHE)
        tarball.unlink()
    return pkg


def main():
    needed = vocabulary_chars()
    OUT.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in OUT.glob("*.json")}
    missing_local = needed - have
    no_data = []
    if missing_local:
        src = source_dir()
        for ch in sorted(missing_local):
            f = src / f"{ch}.json"
            if f.exists():
                shutil.copyfile(f, OUT / f"{ch}.json")
            else:
                no_data.append(ch)
    removed = sorted(have - needed)
    for ch in removed:
        (OUT / f"{ch}.json").unlink()
    total = sum(p.stat().st_size for p in OUT.glob("*.json"))
    print(f"hanzi data: {len(needed)} characters needed, {len(missing_local) - len(no_data)} copied, "
          f"{len(removed)} removed, {len(list(OUT.glob('*.json')))} files, {total / 1024 / 1024:.1f} MB")
    print("characters with no stroke data:", "".join(no_data) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
