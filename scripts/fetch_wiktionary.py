"""Collect Han-Viet readings for every distinct character in the vocabulary from English Wiktionary's
{{vi-readings}} template (Unihan kVietnamese turned out to mix Nom readings in and miss common characters).

Results are cached in data/wiktionary_hanviet.json:
  { char: {"title": "<entry used>", "hanviet": ["ái", "áy"], "weak": false} }
`weak` = the entry only has the older `reading=` list (Han-Viet and Nom mixed, unordered).
Titles tried per character: the character itself first, then its traditional variants.
Re-running only fetches characters missing from the cache.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from hanviet import CJK, ROOT, load_unihan

CACHE = ROOT / "data" / "wiktionary_hanviet.json"
API = "https://en.wiktionary.org/w/api.php?"
UA = {"User-Agent": "hsk-flashcards-build/0.1 (personal study project)"}
BATCH = 50


def fetch(titles):
    q = urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "titles": "|".join(titles), "format": "json", "formatversion": "2", "redirects": "1"})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(API + q, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = int(e.headers.get("Retry-After", 30 * (attempt + 1)))
            print(f"429, waiting {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError("Wiktionary kept rate-limiting")


def parse(content):
    m = re.search(r"\{\{vi-readings(.*?)\n?\}\}", content, re.S)
    if not m:
        return None
    body = m.group(1)

    def items(param):
        mm = re.search(r"\|\s*" + param + r"\s*=([^\n|]*)", body)
        out = []
        if mm:
            for item in mm.group(1).split(","):
                syl = re.sub(r"\[\[|\]\]", "", item).strip().split("-")[0].split(" ")[0].strip().lower()
                if syl and syl not in out:
                    out.append(syl)
        return out

    strong = items("hanviet") or items("hv")
    if strong:  # parameter explicitly labelled Han-Viet
        return {"hanviet": strong, "weak": False}
    mixed = items("readings") or items("reading")  # older format: Han-Viet and Nom readings mixed
    if mixed:
        return {"hanviet": mixed, "weak": True}
    return None


def main():
    _, trad, _ = load_unihan()
    chars = set()
    for level in range(1, 6):
        raw = json.loads((ROOT / "data" / "raw" / f"hsk{level}.json").read_text(encoding="utf-8"))
        for w in raw["words"]:
            chars.update(c for c in w["hanzi"] if CJK.match(c) and c != "儿")
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = sorted(c for c in chars if c not in cache)
    print(f"distinct chars: {len(chars)}, to fetch: {len(todo)}", flush=True)
    titles = {c: [c] + [t for t in trad.get(c, []) if t != c] for c in todo}
    all_titles = sorted({t for ts in titles.values() for t in ts})
    pages = {}
    for i in range(0, len(all_titles), BATCH):
        d = fetch(all_titles[i:i + BATCH])["query"]
        redirects = {r["from"]: r["to"] for r in d.get("redirects", [])}
        for p in d["pages"]:
            if not p.get("missing"):
                pages[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
        for src, dst in redirects.items():
            if dst in pages:
                pages.setdefault(src, pages[dst])
        print(f"{min(i + BATCH, len(all_titles))}/{len(all_titles)} titles", flush=True)
        time.sleep(3)
    for c in todo:
        res = None
        for t in titles[c]:
            if t in pages and (res := parse(pages[t])):
                res["title"] = t
                break
        cache[c] = res or {"title": None, "hanviet": [], "weak": False}
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    missing = sorted(c for c in chars if not cache[c]["hanviet"])
    print(f"without any Wiktionary reading: {len(missing)} {''.join(missing)}")
    print(f"weak (reading= only): {sum(cache[c]['weak'] for c in chars)}")


if __name__ == "__main__":
    main()
