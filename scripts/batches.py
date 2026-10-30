"""Cut word batches for the example-writer subagent and merge its output back.

  python scripts/batches.py cut N       write data/batches/hsk{N}_{from}-{to}.in.json (50 words each) for every
                                        batch whose .out.json does not exist yet
  python scripts/batches.py merge N     merge every hsk{N}_*.out.json into data/enriched/hsk{N}.json
  python scripts/batches.py retry N     cut ONE retry batch (hsk{N}_retry1.in.json) from words whose example is
                                        flagged by validate.py; merge it with `merge` afterwards
  python scripts/batches.py status N    show batches and which are done

Words with reviewed=true are never overwritten. Run scripts/validate.py after every merge.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH_DIR = ROOT / "data" / "batches"
SIZE = 50
# flags that mean "the example sentence itself is bad" (hanviet flags are not the writer's job)
# Quan's Phase 3 decision: out-of-level characters and duplicate sentences are acceptable, so they are NOT
# retried (the validator still reports them). Only structural errors cost a retry.
EXAMPLE_FLAG_PREFIXES = ("câu không chứa", "quá dài", "pinyin", "vi trống", "thiếu câu ví dụ")


def enriched_path(level):
    return ROOT / "data" / "enriched" / f"hsk{level}.json"


def load(level):
    return json.loads(enriched_path(level).read_text(encoding="utf-8"))


def to_input(w, level, note=None):
    item = {"id": w["id"], "hanzi": w["hanzi"], "pinyin": w["pinyin"], "pos": w.get("pos", ""),
            "meaning": w["meaning"], "level": level}
    if note:
        item["retry_note"] = note
    return item


def cut(level):
    data = load(level)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    words = data["words"]
    made = []
    for i in range(0, len(words), SIZE):
        chunk = words[i:i + SIZE]
        name = f"hsk{level}_{i + 1:04d}-{i + len(chunk):04d}"
        if (BATCH_DIR / f"{name}.out.json").exists():
            continue
        todo = [w for w in chunk if not w.get("example") and not w.get("reviewed")]
        if not todo:
            continue
        (BATCH_DIR / f"{name}.in.json").write_text(
            json.dumps([to_input(w, level) for w in todo], ensure_ascii=False, indent=1), encoding="utf-8")
        made.append(name)
    print(f"{len(made)} batch(es) cut for HSK{level}:", ", ".join(made) or "-")


def merge(level):
    data = load(level)
    by_id = {w["id"]: w for w in data["words"]}
    merged = skipped = 0
    for path in sorted(BATCH_DIR.glob(f"hsk{level}_*.out.json")):
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"!! {path.name}: invalid JSON ({e}); delete it and re-run the batch")
            continue
        for item in items:
            w = by_id.get(item.get("id"))
            ex = item.get("example") or {}
            if not w or not ex.get("zh"):
                print(f"!! {path.name}: skipping {item.get('id')} (unknown id or empty example)")
                skipped += 1
                continue
            if w.get("reviewed"):
                continue
            w["example"] = {"zh": ex["zh"].strip(), "pinyin": ex.get("pinyin", "").strip(), "vi": ex.get("vi", "").strip()}
            if not w.get("pos") and item.get("pos"):  # only fills empty pos (HSK4-5)
                w["pos"] = item["pos"].strip()
            merged += 1
    enriched_path(level).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"HSK{level}: merged {merged} examples, skipped {skipped}; now {sum(1 for w in data['words'] if w.get('example'))}/{len(data['words'])} have one")


def retry(level):
    data = load(level)
    items = []
    for w in data["words"]:
        bad = [f for f in w.get("flags", []) if f.startswith(EXAMPLE_FLAG_PREFIXES)]
        if bad and not w.get("reviewed"):
            old = (w.get("example") or {}).get("zh", "")
            items.append(to_input(w, level, f"previous sentence '{old}' was rejected: {'; '.join(bad)}. Write a different sentence."))
    path = BATCH_DIR / f"hsk{level}_retry1.in.json"
    if (BATCH_DIR / f"hsk{level}_retry1.out.json").exists():
        sys.exit("retry already done once for this level (hsk%d_retry1.out.json exists)" % level)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{path.name}: {len(items)} words to retry")


def status(level):
    ins = sorted(BATCH_DIR.glob(f"hsk{level}_*.in.json"))
    for p in ins:
        out = p.with_name(p.name.replace(".in.json", ".out.json"))
        print(("done   " if out.exists() else "PENDING"), p.name)
    print(f"{len(ins)} batches")


if __name__ == "__main__":
    cmd, lv = sys.argv[1], int(sys.argv[2])
    {"cut": cut, "merge": merge, "retry": retry, "status": status}[cmd](lv)
