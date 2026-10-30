"""Validate data/enriched/hsk{N}.json and write flags into each word's `flags` list (never auto-fixes).

Usage: python scripts/validate.py [N ...] [--require-examples]
Without levels, validates all five. Example checks only run for words that have an example, unless
--require-examples is given (then a missing example is flagged too).
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CJK = re.compile(r"[㐀-鿿\U00020000-\U0002ffff]")
ALLOWED_EXTRA = set("，。！？、；：“”‘’\"'…—-·（）() 0123456789,.!?;:%/")
MAX_LEN = {1: 10, 2: 10, 3: 15, 4: 15, 5: 15}
TONE_MARKS = set("āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ")


def load(level, folder="enriched"):
    return json.loads((ROOT / "data" / folder / f"hsk{level}.json").read_text(encoding="utf-8"))


def count_syllables(pinyin):
    """Syllables = vowel groups, split by apostrophes; a trailing erhua 'r' adds none."""
    text = unicodedata.normalize("NFD", pinyin.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    n = 0
    for chunk in re.split(r"[^a-züv]+", text):
        n += len(re.findall(r"[aeiouüv]+", chunk))
    return n


def target_forms(hanzi):
    """Accepted spellings of the target word (parenthesised parts optional)."""
    forms = {re.sub(r"[()（）]", "", hanzi), re.sub(r"[(（][^)）]*[)）]", "", hanzi)}
    return {f for f in forms if f}


def is_split_form(zh, hanzi):
    if len(hanzi) == 2 and hanzi not in zh:
        a, b = hanzi
        return re.search(re.escape(a) + r".{1,3}" + re.escape(b), zh) is not None
    return False


def validate_level(level, require_examples, vocab_chars, all_examples):
    data = load(level)
    counts = Counter()
    for w in data["words"]:
        flags = []
        hv = w.get("hanviet", "")
        if not hv or "?" in hv:
            flags.append("hanviet trống/thiếu")
        else:
            syl = len(re.sub(r"[()（）]", " ", hv).split())
            if syl != len(CJK.findall(w["hanzi"])):
                flags.append("hanviet: số âm tiết ≠ số chữ")
        if w.get("hanviet_check"):
            flags.append("hanviet cần kiểm tra")
        ex = w.get("example")
        if not ex:
            if require_examples:
                flags.append("thiếu câu ví dụ")
        else:
            zh, py, vi = ex.get("zh", ""), ex.get("pinyin", ""), ex.get("vi", "")
            if not vi.strip():
                flags.append("vi trống")
            if not any(f in zh for f in target_forms(w["hanzi"])):
                if is_split_form(zh, w["hanzi"]):
                    flags.append("dạng tách (từ ly hợp)")
                else:
                    flags.append("câu không chứa từ mục tiêu")
            bad = sorted({c for c in zh if c not in vocab_chars and c not in ALLOWED_EXTRA})
            if bad:
                flags.append("chữ ngoài từ vựng ≤ HSK%d: %s" % (level, "".join(bad)))
            zh_chars = CJK.findall(zh)
            if len(zh_chars) > MAX_LEN[level]:
                flags.append(f"quá dài ({len(zh_chars)} > {MAX_LEN[level]})")
            n_py = count_syllables(py)
            n_zh = len(zh_chars)
            erhua_ok = "儿" in zh and n_py == n_zh - zh.count("儿")
            if n_py != n_zh and not erhua_ok:
                flags.append(f"pinyin: {n_py} âm tiết ≠ {n_zh} chữ")
            if re.search(r"[0-9]", py):
                flags.append("pinyin có số")
            for tok in py.split():
                if count_syllables(tok) >= 2 and not (set(tok.lower()) & TONE_MARKS):
                    flags.append(f"pinyin thiếu dấu thanh: {tok}")
                    break
            if all_examples[zh] > 1:
                flags.append("câu ví dụ trùng")
        w["flags"] = flags
        for f in flags:
            counts[f.split(":")[0].split(" (")[0]] += 1
    (ROOT / "data" / "enriched" / f"hsk{level}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    flagged = sum(1 for w in data["words"] if w["flags"])
    print(f"HSK{level}: {len(data['words'])} words, {flagged} flagged")
    for k, v in counts.most_common():
        print(f"   {v:5d}  {k}")
    return flagged


def main():
    args = sys.argv[1:]
    require = "--require-examples" in args
    levels = [int(a) for a in args if a.isdigit()] or [1, 2, 3, 4, 5]
    raw_chars = {}
    for lv in range(1, 6):
        raw_chars[lv] = {c for w in load(lv, "raw")["words"] for c in w["hanzi"] if CJK.match(c)}
    all_examples = Counter()
    for lv in range(1, 6):
        for w in load(lv)["words"]:
            if w.get("example"):
                all_examples[w["example"]["zh"]] += 1
    for lv in levels:
        vocab = set().union(*(raw_chars[i] for i in range(1, lv + 1)))
        validate_level(lv, require, vocab, all_examples)


if __name__ == "__main__":
    main()
