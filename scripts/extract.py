"""Extract Data_HSK1..5 sheets from source/vocab.xlsx into data/raw/hsk{N}.json."""
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {1: 500, 2: 772, 3: 973, 4: 1000, 5: 1300}


def main():
    wb = openpyxl.load_workbook(ROOT / "source" / "vocab.xlsx", read_only=True, data_only=True)
    out_dir = ROOT / "data" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    for level, expected in EXPECTED.items():
        ws = wb[f"Data_HSK{level}"]
        words = []
        for row in ws.iter_rows(min_row=2, max_col=6, values_only=True):
            stt, hanzi, pinyin, pos, meaning, accept = (row + (None,) * 6)[:6]
            if hanzi is None or str(hanzi).strip() == "":
                break  # empty pre-formatted rows
            hanzi = str(hanzi).strip()
            pinyin = str(pinyin or "").strip()
            accept_list = [a.strip() for a in re.split(r"[;；]", str(accept or "")) if a.strip()]
            for must in (hanzi, pinyin):
                if must and must not in accept_list:
                    accept_list.insert(0, must) if must == hanzi else accept_list.insert(1, must)
            words.append({
                "id": f"{level}-{int(stt):04d}",
                "hanzi": hanzi,
                "pinyin": pinyin,
                "pos": str(pos or "").strip(),
                "meaning": str(meaning or "").strip(),
                "accept": accept_list,
            })
        assert len(words) == expected, f"HSK{level}: {len(words)} != {expected}"
        assert len({w["id"] for w in words}) == len(words), f"HSK{level}: duplicate ids"
        (out_dir / f"hsk{level}.json").write_text(
            json.dumps({"level": level, "count": len(words), "words": words}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"HSK{level}: {len(words)} words, empty pos: {sum(1 for w in words if not w['pos'])}")


if __name__ == "__main__":
    main()
