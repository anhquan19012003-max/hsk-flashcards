"""Apply Quan's edits from review/hsk{N}_review.xlsx back to data/enriched/hsk{N}.json.

Usage: python scripts/import_review.py N
Only cells that differ from the JSON are applied (matched by id, never by hanzi). Edited words get
reviewed=true so later script runs never overwrite them. A non-empty "Ghi chú / sửa" cell is stored in
`note` and printed so the instruction can be acted on. Re-run validate.py and build.py afterwards.
"""
import json
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent


def main():
    level = int(sys.argv[1])
    path = ROOT / "data" / "enriched" / f"hsk{level}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    by_id = {w["id"]: w for w in data["words"]}
    ws = openpyxl.load_workbook(ROOT / "review" / f"hsk{level}_review.xlsx", data_only=True).active
    changed = notes = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        wid, _, _, _, pos, hanviet, zh, py, vi, _, _, note = (list(row) + [None] * 12)[:12]
        w = by_id.get(wid)
        if not w:
            print(f"skip unknown id {wid}")
            continue
        clean = lambda v: "" if v is None else str(v).strip()
        edits = {}
        if clean(pos) != w.get("pos", ""):
            edits["pos"] = clean(pos)
        if clean(hanviet) != w.get("hanviet", ""):
            edits["hanviet"] = clean(hanviet)
        old = w.get("example") or {}
        new_ex = {"zh": clean(zh), "pinyin": clean(py), "vi": clean(vi)}
        if any(new_ex.values()) and new_ex != {k: old.get(k, "") for k in new_ex}:
            edits["example"] = new_ex
        if edits:
            w.update(edits)
            w["reviewed"] = True
            if "hanviet" in edits:
                w["hanviet_check"] = False
                w.pop("hanviet_note", None)
            changed += 1
        if clean(note) and clean(note) != w.get("note"):
            w["note"] = clean(note)
            notes += 1
            print(f"{wid} {w['hanzi']}: {clean(note)}")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"HSK{level}: {changed} words edited, {notes} new notes")


if __name__ == "__main__":
    main()
