"""Build docs/data/hsk{N}.json from data/enriched (no flags or working fields).

Usage: python scripts/build.py [N ...]
"""
import json
import sys
from pathlib import Path

import build_hanzi_data

ROOT = Path(__file__).resolve().parent.parent


def main():
    levels = [int(a) for a in sys.argv[1:]] or [1, 2, 3, 4, 5]
    out_dir = ROOT / "docs" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    for lv in levels:
        data = json.loads((ROOT / "data" / "enriched" / f"hsk{lv}.json").read_text(encoding="utf-8"))
        words = []
        for w in data["words"]:
            hv = w.get("hanviet", "")
            item = {"id": w["id"], "hanzi": w["hanzi"], "pinyin": w["pinyin"], "pos": w.get("pos", ""),
                    "meaning": w["meaning"], "accept": w["accept"],
                    "hanviet": "" if "?" in hv else hv}  # unresolved readings stay hidden in the app
            ex = w.get("example")
            if ex and ex.get("zh"):
                item["example"] = {"zh": ex["zh"], "pinyin": ex.get("pinyin", ""), "vi": ex.get("vi", "")}
            words.append(item)
        (out_dir / f"hsk{lv}.json").write_text(
            json.dumps({"level": lv, "count": len(words), "words": words}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        print(f"HSK{lv}: {len(words)} words, {sum('example' in w for w in words)} with example")
    build_hanzi_data.main()  # stroke data for every character in the vocabulary


if __name__ == "__main__":
    main()
