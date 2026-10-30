"""Validate an extracted paper (specs/mock-tests.md section 3).

  python scripts/bank/validate_paper.py <work/paper-id[/questions.json]> ...

Errors (exit 1): wrong numbering or counts per part, invalid answers, missing files/shared options, bad structure.
Warnings: missing explanations or listening scripts.
"""
import itertools
import json
import re
import sys
from pathlib import Path

SKILL_TYPES = {"tf": {"nghe"}, "choice": {"nghe", "doc"}, "wordbank": {"doc"}, "order-sentences": {"sapxep"}, "order-words": {"sapxep"}}

# (first number, last number, skill, type) per exam format. Question number = trailing integer of the question id.
PROFILES = {
    ("HSK 2.0", 4): [
        (1, 10, "nghe", "tf"), (11, 45, "nghe", "choice"),
        (46, 55, "doc", "wordbank"), (56, 65, "sapxep", "order-sentences"), (66, 85, "doc", "choice"),
        (86, 95, "sapxep", "order-words"),
    ],
}

PUNCT = re.compile(r"[\s。？！，、；：．.?!,;:\"'“”‘’（）()\[\]【】—…·《》]")


def norm(s: str) -> str:
    return PUNCT.sub("", s or "")


def can_form(answer: str, tiles) -> bool:
    """True if `answer` (ignoring spaces/punctuation) is a concatenation of ALL the tiles in some order."""
    target = norm(answer)
    texts = [norm(t) for t in tiles]
    if sum(len(t) for t in texts) != len(target):
        return False
    for perm in set(itertools.permutations(texts)):
        if "".join(perm) == target:
            return True
    return False


def qnum(qid: str):
    m = re.search(r"-(\d+)$", qid)
    return int(m.group(1)) if m else None


def validate(data: dict, base: Path):
    errors, warnings = [], []
    err = errors.append
    paper = data.get("paper") or {}
    pid = paper.get("id")
    if not pid:
        err("paper.id missing")
        pid = ""
    if "level" not in paper:
        err("paper.level missing")
    seen = {}
    unit_ids = set()

    def need_file(rel, where):
        if rel and not (base / rel).is_file():
            err(f"{where}: file not found: {rel}")

    for u in data.get("units", []):
        uid = u.get("id", "?")
        if uid in unit_ids:
            err(f"{uid}: duplicate unit id")
        unit_ids.add(uid)
        t, skill = u.get("type"), u.get("skill")
        if t not in SKILL_TYPES:
            err(f"{uid}: unknown type {t!r}")
            continue
        if skill not in SKILL_TYPES[t]:
            err(f"{uid}: type {t} cannot be in tab {skill!r}")
        ctx = u.get("context") or {}
        shared = ctx.get("sharedOptions") or []
        shared_keys = [o.get("key") for o in shared]
        need_file(ctx.get("audio"), uid)
        need_file(ctx.get("image"), uid)
        for o in shared:
            need_file(o.get("image"), f"{uid} shared option {o.get('key')}")
        qs = u.get("questions") or []
        if not qs:
            err(f"{uid}: no questions")
        if t == "wordbank" and not shared:
            err(f"{uid}: wordbank unit has no sharedOptions")
        nums = [qnum(q.get("id", "")) for q in qs]
        if None in nums:
            err(f"{uid}: question id must end in -<number>")
        elif nums != list(range(nums[0], nums[0] + len(nums))):
            err(f"{uid}: question numbers in a unit must be consecutive: {nums}")
        for q in qs:
            qid = q.get("id", "?")
            if qid in seen:
                err(f"{qid}: duplicate question id")
            seen[qid] = (u, q)
            if pid and not qid.startswith(pid + "-"):
                err(f"{qid}: id must start with {pid}-")
            excluded = bool(q.get("exclude"))
            ans = q.get("answer")
            opts = q.get("options")
            keys = [o.get("key") for o in opts] if opts else shared_keys
            need_file(q.get("audio"), qid)
            for o in opts or []:
                need_file(o.get("image"), f"{qid} option {o.get('key')}")
            if t != "tf" and not opts and not shared:
                err(f"{qid}: no options and the unit has no sharedOptions")
            if t == "tf":
                if ans not in ("✓", "✗"):
                    err(f"{qid}: tf answer must be ✓ or ✗, got {ans!r}")
                if not q.get("prompt"):
                    err(f"{qid}: tf statement (prompt) is empty")
            elif t in ("choice", "wordbank"):
                if ans not in keys:
                    err(f"{qid}: answer {ans!r} is not one of the options {keys}")
                if t == "choice" and skill == "doc" and not q.get("prompt") and not ctx.get("text"):
                    err(f"{qid}: reading question has neither prompt nor passage")
                if t == "wordbank" and opts:
                    err(f"{qid}: wordbank questions use the unit's sharedOptions (options must be null)")
            elif t == "order-sentences":
                if not opts or sorted(keys) != sorted(set(keys)) or len(keys) < 2:
                    err(f"{qid}: order-sentences needs distinct sentence options")
                elif not isinstance(ans, str) or sorted(ans) != sorted(keys):
                    err(f"{qid}: answer {ans!r} is not a permutation of {keys}")
            elif t == "order-words":
                tiles = [o.get("text", "") for o in opts or []]
                if not tiles:
                    err(f"{qid}: order-words needs tiles")
                else:
                    for a in [ans] + list(q.get("alsoAccept") or []):
                        if not isinstance(a, str) or not can_form(a, tiles):
                            err(f"{qid}: {a!r} is not made of exactly the given tiles")
            if skill == "nghe" and not excluded and not (q.get("audio") or ctx.get("audio")):
                err(f"{qid}: listening question has no audio clip (exclude it with a reason if the clip is bad)")
            if skill == "nghe" and not (q.get("script") or ctx.get("script")):
                warnings.append(f"{qid}: no listening script")
            if not q.get("explain_vi"):
                warnings.append(f"{qid}: no explain_vi")

    prof = PROFILES.get((paper.get("examVersion"), paper.get("level")))
    if prof is None:
        warnings.append(f"no numbering profile for {paper.get('examVersion')} level {paper.get('level')}: only generic checks ran")
    else:
        expected = {}
        for lo, hi, skill, t in prof:
            for n in range(lo, hi + 1):
                expected[n] = (skill, t)
        got = {}
        for qid, (u, q) in seen.items():
            n = qnum(qid)
            if n is not None:
                got[n] = (u.get("skill"), u.get("type"))
        missing = sorted(set(expected) - set(got))
        extra = sorted(set(got) - set(expected))
        if missing:
            err(f"missing question numbers: {missing}")
        if extra:
            err(f"unexpected question numbers (not in the paper): {extra}")
        for n in sorted(set(expected) & set(got)):
            if expected[n] != got[n]:
                err(f"question {n}: expected {expected[n]} but found {got[n]}")
    return errors, warnings, seen


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    bad = 0
    for a in args:
        p = Path(a)
        f = p / "questions.json" if p.is_dir() else p
        data = json.loads(f.read_text(encoding="utf-8"))
        errors, warnings, seen = validate(data, f.parent)
        per = {}
        for u, q in seen.values():
            per[u["skill"]] = per.get(u["skill"], 0) + 1
        print(f"{data['paper'].get('id')}: {len(seen)} questions {per}, {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print("  ERROR", e)
        for w in warnings[:15]:
            print("  warn ", w)
        if len(warnings) > 15:
            print(f"  ... {len(warnings) - 15} more warnings")
        bad += bool(errors)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
