"""Build data/enriched/hsk{N}.json from data/raw, filling `hanviet` from Unicode Unihan kVietnamese.

Per character: collect kVietnamese readings of the character itself plus its traditional variants
(kTraditionalVariant / kSimplifiedVariant). One reading -> automatic. Several readings -> resolve with
POLYPHONE (pinyin-syllable based) or fall back to the first reading and set hanviet_check. No reading ->
hanviet_check with a '?' placeholder, never a silent guess.

Re-running keeps any `example`/`pos` already present in data/enriched (it only refreshes hanviet fields
for words not yet reviewed).
"""
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNIHAN = ROOT / "data" / "unihan"

# Polyphonic characters: char -> [(tone-marked pinyin syllable that must occur in the word's pinyin, reading)].
# First matching entry wins; if none matches, the word is flagged hanviet_check.
POLYPHONE = {
    "行": [("háng", "hàng"), ("xíng", "hành"), ("xìng", "hạnh")],
    "长": [("zhǎng", "trưởng"), ("cháng", "trường")],
    "乐": [("yuè", "nhạc"), ("lè", "lạc")],
    "好": [("hào", "hiếu"), ("hǎo", "hảo")],
    "重": [("chóng", "trùng"), ("zhòng", "trọng")],
    "调": [("diào", "điệu"), ("tiáo", "điều")],
    "为": [("wèi", "vị"), ("wéi", "vi")],
    "了": [("liǎo", "liễu"), ("le", "liễu")],
    "着": [("zhe", "trước"), ("zháo", "trước"), ("zhuó", "trước")],
    "得": [("děi", "đắc"), ("de", "đắc"), ("dé", "đắc")],
    "地": [("de", "địa"), ("dì", "địa")],
    "还": [("hái", "hoàn"), ("huán", "hoàn")],
    "干": [("gān", "can"), ("gàn", "cán")],
    "没": [("méi", "một"), ("mò", "một")],
    "都": [("dōu", "đô"), ("dū", "đô")],
    "和": [("hé", "hòa"), ("huó", "hòa"), ("huò", "hòa"), ("hè", "họa"), ("hú", "hòa")],
    "发": [("fā", "phát"), ("fà", "phát")],
    "觉": [("jiào", "giác"), ("jué", "giác")],
    "教": [("jiāo", "giáo"), ("jiào", "giáo")],
    "数": [("shǔ", "sổ"), ("shù", "số"), ("shuò", "sác")],
    "分": [("fèn", "phận"), ("fēn", "phân")],
    "假": [("jià", "giá"), ("jiǎ", "giả")],
    "角": [("jué", "giác"), ("jiǎo", "giác")],
    "朝": [("cháo", "triều"), ("zhāo", "triêu")],
    "种": [("zhǒng", "chủng"), ("zhòng", "chủng")],
    "传": [("zhuàn", "truyện"), ("chuán", "truyền")],
    "便": [("pián", "tiện"), ("biàn", "tiện")],
    "差": [("chà", "sai"), ("chā", "sai"), ("chāi", "sai"), ("cī", "si")],
    "宁": [("nìng", "ninh"), ("níng", "ninh")],
    "背": [("bēi", "bội"), ("bèi", "bối")],
    "弹": [("tán", "đàn"), ("dàn", "đạn")],
    "处": [("chù", "xứ"), ("chǔ", "xử")],
    "切": [("qiè", "thiết"), ("qiē", "thiết")],
    "咳": [("hāi", "khái"), ("ké", "khái")],
    "那": [("nà", "na"), ("nèi", "na")],
    "什": [("shén", "thập"), ("shí", "thập")],
    "几": [("jǐ", "kỷ"), ("jī", "ki")],
    "喝": [("hē", "hát"), ("hè", "hát")],
    "载": [("zǎi", "tái"), ("zài", "tải")],
    "率": [("lǜ", "suất"), ("shuài", "suất")],
    "否": [("fǒu", "phủ"), ("pǐ", "bĩ")],
    "会": [("kuài", "cối"), ("huì", "hội")],
    "合": [("hé", "hợp"), ("gě", "hợp")],
    "量": [("liàng", "lượng"), ("liáng", "lương")],
    "藏": [("zàng", "tạng"), ("cáng", "tàng")],
    "晕": [("yùn", "vựng"), ("yūn", "vựng")],
    "累": [("lěi", "lũy"), ("lèi", "lụy"), ("léi", "luy")],
    "难": [("nán", "nan"), ("nàn", "nạn")],
    "相": [("xiāng", "tương"), ("xiàng", "tướng")],
    "空": [("kòng", "không"), ("kōng", "không")],
    "更": [("gèng", "cánh"), ("gēng", "canh")],
    "应": [("yīng", "ưng"), ("yìng", "ứng")],
    "冲": [("chōng", "xung"), ("chòng", "xung")],
    "磨": [("mó", "ma"), ("mò", "ma")],
    "模": [("mó", "mô"), ("mú", "mô")],
    "露": [("lòu", "lộ"), ("lù", "lộ")],
    "薄": [("báo", "bạc"), ("bó", "bạc")],
    "挑": [("tiāo", "khiêu"), ("tiǎo", "khiêu")],
    "扇": [("shàn", "phiến"), ("shān", "phiến")],
    "炸": [("zhá", "tạc"), ("zhà", "tạc")],
    "转": [("zhuǎn", "chuyển"), ("zhuàn", "chuyển")],
    "参": [("cān", "tham"), ("cēn", "sâm"), ("shēn", "sâm")],
    "称": [("chēng", "xưng"), ("chèn", "xứng")],
}

# Characters whose Wiktionary entry (older `reading=` format) lists Han-Viet and Nom readings together.
# CHOICE picks the Han-Viet reading from those sourced candidates (must be one of them, else ignored).
CHOICE = {
    "临": "lâm", "亚": "á", "亮": "lượng", "仅": "cận", "伙": "hoả", "但": "đãn", "何": "hà", "俩": "lưỡng",
    "值": "trị", "做": "tố", "偷": "thâu", "净": "tịnh", "击": "kích", "刚": "cương", "办": "biện",
    "劣": "liệt", "启": "khải", "告": "cáo", "咨": "tư", "嗓": "tảng", "够": "cấu", "套": "sáo",
    "妨": "phương", "它": "tha", "屿": "dữ", "巨": "cự", "幸": "hạnh", "弯": "loan", "归": "quy",
    "很": "ngận", "悠": "du", "慧": "tuệ", "戴": "đái", "抖": "đẩu", "抢": "thương", "挡": "đáng",
    "挤": "tễ", "握": "ác", "摔": "suất", "撕": "tê", "操": "thao", "改": "cải", "既": "ký", "旧": "cựu",
    "暑": "thử", "暖": "noãn", "桌": "trác", "桔": "cát", "梦": "mộng", "椅": "ỷ", "汇": "hối",
    "爱": "ái", "爸": "bả", "疼": "đông", "痒": "dưỡng", "皂": "tạo", "盐": "diêm", "睁": "tranh",
    "瞎": "hạt", "碗": "oản", "窄": "trách", "笑": "tiếu", "笨": "bổn", "签": "thiêm", "糟": "tao",
    "绸": "trù", "综": "tổng", "缓": "hoãn", "而": "nhi", "肉": "nhục", "肠": "trường", "胡": "hồ",
    "脖": "bột", "脸": "kiểm", "菜": "thái", "营": "doanh", "街": "nhai", "裔": "duệ", "该": "cai",
    "赛": "tái", "赶": "cản", "跑": "bào", "蹲": "đôn", "较": "giảo", "辆": "lượng", "这": "giá",
    "遍": "biến", "邮": "bưu", "醉": "túy", "量": "lượng", "铃": "linh", "锻": "đoán", "问": "vấn",
    "闻": "văn", "阿": "a", "陌": "mạch", "震": "chấn", "鞭": "tiên", "页": "hiệt", "频": "tần",
    "颗": "khỏa", "餐": "xan", "饭": "phạn", "饺": "giảo", "饿": "ngạ", "鼠": "thử", "衡": "hành",
    "率": "suất", "藏": "tàng", "食": "thực", "假": "giả",
    "百": "bách", "对": "đối", "第": "đệ", "东": "đông", "干": "can", "看": "khán", "校": "hiệu",
    "准": "chuẩn", "须": "tu", "示": "thị", "租": "tô", "于": "vu", "园": "viên", "钟": "chung",
    "借": "tá", "离": "li", "响": "hưởng", "眼": "nhãn", "只": "chỉ", "剧": "kịch", "据": "cứ",
    "每": "mỗi", "沙": "sa", "死": "tử", "艺": "nghệ", "湿": "thấp", "担": "đảm", "激": "kích",
    "案": "án", "折": "chiết", "恶": "ác", "卷": "quyển", "疗": "liệu", "研": "nghiên", "丑": "sửu",
    "涂": "đồ", "忆": "ức", "筑": "trúc", "浇": "kiêu", "托": "thác", "洒": "sái", "舍": "xá",
    "拐": "quải", "捐": "quyên", "洲": "châu", "盆": "bồn",
}
# Same idea, but the pick is a guess among the candidates -> the word is still flagged hanviet_check.
LOWCONF = {
    "卡": "tạp", "征": "chinh", "璃": "lê", "啤": "bì", "悄": "tiễu", "档": "đang", "烫": "năng", "甩": "suý", "碰": "bính",
    "霉": "mai", "靠": "kháo", "傻": "xoạ", "哎": "ngáy", "贷": "thải",
}

from hanviet_choices import CHOICE as _CHOICE2, LOWCONF as _LOWCONF2  # noqa: E402

CHOICE.update(_CHOICE2)
LOWCONF.update(_LOWCONF2)

# More polyphonic characters: pinyin syllable that must occur in the word -> reading.
POLYPHONE.update({
    "少": [("shào", "thiếu"), ("shǎo", "thiểu")],
    "降": [("xiáng", "hàng"), ("jiàng", "giáng")],
    "将": [("jiàng", "tướng"), ("jiāng", "tương")],
    "散": [("sàn", "tán"), ("sǎn", "tản")],
    "与": [("yù", "dự"), ("yǔ", "dữ")],
    "斗": [("dǒu", "đẩu"), ("dòu", "đấu")],
    "占": [("zhān", "chiêm"), ("zhàn", "chiếm")],
    "冠": [("guàn", "quán"), ("guān", "quan")],
    "中": [("zhòng", "trúng"), ("zhōng", "trung")],
    "要": [("yāo", "yêu"), ("yào", "yếu")],
    "圈": [("juàn", "quyển"), ("quān", "khuyên")],
    "拆": [("chāi", "sách")],
})

_OLD_STYLE = {"òa": "oà", "óa": "oá", "ỏa": "oả", "õa": "oã", "ọa": "oạ", "òe": "oè", "óe": "oé", "ỏe": "oẻ",
              "õe": "oẽ", "ọe": "oẹ", "ùy": "uỳ", "úy": "uý", "ủy": "uỷ", "ũy": "uỹ", "ụy": "uỵ"}


def skey(s):
    """Spelling-style-insensitive key: hòa == hoà, thủy == thuỷ. Output uses this old-style spelling too."""
    s = unicodedata.normalize("NFC", s)
    for new, old in _OLD_STYLE.items():
        s = s.replace(new, old)
    return s


def pick(cands, want):
    """The sourced candidate matching `want` (ignoring accent-placement style), else None."""
    k = skey(want)
    return next((c for c in cands if skey(c) == k), None)


CJK = re.compile(r"[㐀-鿿\U00020000-\U0002ffff]")


def load_unihan():
    viet = defaultdict(list)
    for line in (UNIHAN / "Unihan_Readings.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cp, field, value = line.split("\t", 2)
        if field == "kVietnamese":
            ch = chr(int(cp[2:], 16))
            for r in value.split():
                if r not in viet[ch]:
                    viet[ch].append(r)
    trad = defaultdict(list)  # simplified -> traditional variants
    simp = defaultdict(list)  # traditional -> simplified variants (so we can also reach z-variants)
    for line in (UNIHAN / "Unihan_Variants.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cp, field, value = line.split("\t", 2)
        ch = chr(int(cp[2:], 16))
        if field == "kTraditionalVariant":
            trad[ch] += [chr(int(v[2:], 16)) for v in value.split()]
        elif field == "kSimplifiedVariant":
            simp[ch] += [chr(int(v[2:], 16)) for v in value.split()]
    return viet, trad, simp


def readings_for(ch, viet, trad):
    out = []
    for c in [ch] + trad.get(ch, []):
        for r in viet.get(c, []):
            if r not in out:
                out.append(r)
    return out


def load_wiktionary():
    path = ROOT / "data" / "wiktionary_hanviet.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for entry in data.values():  # a few entries have stray markup: "kí//ký", "phanh;", "váng<!"
        clean = []
        for item in entry["hanviet"]:
            for part in re.split(r"[/;]+", item):
                if re.fullmatch(r"[a-zà-ỹ]+", part) and part not in clean:
                    clean.append(part)
        entry["hanviet"] = clean
    return data


def load_mandarin():
    """char -> set of Mandarin readings (kHanyuPinyin / kMandarin), used to detect polyphonic characters."""
    out = defaultdict(set)
    for line in (UNIHAN / "Unihan_Readings.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cp, field, value = line.split("\t", 2)
        if field == "kHanyuPinyin":
            ch = chr(int(cp[2:], 16))
            for part in value.split():
                out[ch].update(part.split(":", 1)[-1].split(","))
        elif field == "kMandarin":
            out[chr(int(cp[2:], 16))].update(value.split())
    return out


def polyphonic(ch, mandarin, trad):
    readings = set()
    for c in [ch] + trad.get(ch, []):
        readings |= mandarin.get(c, set())
    return len(readings) > 1


def hanviet_for(hanzi, pinyin, viet, trad, wik, mandarin):
    """Return (hanviet string, check_reason or None)."""
    parts, reasons = [], []
    for ch in hanzi:
        if not CJK.match(ch):
            parts.append(ch)  # parentheses etc. stay as they are
            continue
        weak = unihan_only = False
        if ch == "儿":
            cands = ["nhi"]
        elif wik.get(ch, {}).get("hanviet"):
            cands, weak = wik[ch]["hanviet"], wik[ch]["weak"]
        else:
            cands = readings_for(ch, viet, trad)  # Unihan: may contain Nom readings -> always reviewed
            weak = unihan_only = bool(cands)
        # the tables below only *select* among sourced readings; they never introduce a new one
        if ch in POLYPHONE:
            hit = next((pick(cands, r) for syl, r in POLYPHONE[ch] if syl in pinyin.lower() and pick(cands, r)), None)
            if hit:
                parts.append(skey(hit))
                continue
        if ch in CHOICE and pick(cands, CHOICE[ch]):
            parts.append(skey(pick(cands, CHOICE[ch])))
        elif ch in LOWCONF and pick(cands, LOWCONF[ch]):
            parts.append(skey(pick(cands, LOWCONF[ch])))
            reasons.append(f"{ch}: unsure, candidates {'/'.join(cands)}")
        elif not cands:
            parts.append("?")
            reasons.append(f"no reading for {ch}")
        elif unihan_only:
            parts.append(skey(cands[0]))
            reasons.append(f"{ch}: only Unihan has it: {'/'.join(cands)}")
        elif len(cands) == 1:
            parts.append(skey(cands[0]))
        elif not weak and not polyphonic(ch, mandarin, trad):
            parts.append(skey(cands[0]))  # labelled Han-Viet list, single-reading character: first entry
        else:
            parts.append(skey(cands[0]))
            reasons.append(f"{ch}: {'/'.join(cands)}")
    # join syllables with spaces, but glue parentheses to the neighbouring word: "hữu (nhất) ta"
    text = " ".join(p for p in parts if p not in ("(", ")", "（", "）"))
    if "(" in hanzi or "（" in hanzi:
        text = ""
        for p in parts:
            if p in ("(", "（"):
                text += " (" if text else "("
            elif p in (")", "）"):
                text += ")"
            else:
                text += ("" if text.endswith("(") or not text else " ") + p
    return text, ("; ".join(reasons) or None)


def main():
    viet, trad, _ = load_unihan()
    wik = load_wiktionary()
    mandarin = load_mandarin()
    out_dir = ROOT / "data" / "enriched"
    out_dir.mkdir(parents=True, exist_ok=True)
    total, flagged, missing = 0, 0, 0
    for level in range(1, 6):
        raw = json.loads((ROOT / "data" / "raw" / f"hsk{level}.json").read_text(encoding="utf-8"))
        target = out_dir / f"hsk{level}.json"
        old = {}
        if target.exists():
            old = {w["id"]: w for w in json.loads(target.read_text(encoding="utf-8"))["words"]}
        words = []
        for w in raw["words"]:
            hv, why = hanviet_for(w["hanzi"], w["pinyin"], viet, trad, wik, mandarin)
            nw = dict(w)
            prev = old.get(w["id"], {})
            for key in ("example", "reviewed", "note"):
                if key in prev:
                    nw[key] = prev[key]
            if prev.get("reviewed"):
                nw["pos"] = prev.get("pos", nw["pos"])
                nw["hanviet"] = prev.get("hanviet", hv)
                nw["hanviet_check"] = prev.get("hanviet_check", False)
            else:
                nw["hanviet"] = hv
                nw["hanviet_check"] = bool(why)
                if why:
                    nw["hanviet_note"] = why
            if prev.get("pos") and not nw["pos"]:
                nw["pos"] = prev["pos"]
            words.append(nw)
            total += 1
            flagged += bool(why)
            missing += "?" in hv
        target.write_text(json.dumps({"level": level, "count": len(words), "words": words},
                                     ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"words={total} hanviet_check={flagged} with_missing_reading={missing}")


if __name__ == "__main__":
    main()
