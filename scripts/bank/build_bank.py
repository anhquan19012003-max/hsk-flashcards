"""Build the encrypted question bank: work/*/questions.json (+ clips, images) -> docs/bank/ (specs/mock-tests.md section 5).

  python scripts/bank/build_bank.py [--work DIR] [--out DIR] [--new-salt] [--magic-link]

The password comes from BANK_PASSWORD or <private>/.bank-password and is never printed or stored.
If an existing bank was made with another password the build stops (nothing is written) unless --new-salt is given.
--magic-link prints the `#k=...` part of the unlock link (the derived key). Hand it to Quan in the chat only.
"""
import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bankcrypto as bc  # noqa: E402
from paths import ROOT, get_password, private_dir  # noqa: E402


def natural_key(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def load_papers(work: Path):
    papers = []
    if work.is_dir():
        for d in sorted((p for p in work.iterdir() if p.is_dir() and not p.name.startswith("_")), key=lambda p: natural_key(p.name)):
            f = d / "questions.json"
            if (d / ".hold").exists():  # work in progress (clips or explanations not done yet): not published
                continue
            if f.is_file():
                papers.append((d, json.loads(f.read_text(encoding="utf-8"))))
    return papers


class Writer:
    """Writes encrypted files; skips a file whose current content already decrypts to the same bytes (keeps git diffs small)."""

    def __init__(self, out: Path, key: bytes):
        self.out, self.key = out, key
        self.written = set()
        self.stats = {"new": 0, "same": 0, "bytes": 0}

    def put(self, rel: str, plaintext: bytes) -> int:
        path = self.out / rel
        self.written.add(rel)
        if path.is_file():
            try:
                if bc.decrypt(self.key, path.read_bytes()) == plaintext:
                    self.stats["same"] += 1
                    return path.stat().st_size
            except Exception:
                pass
        path.parent.mkdir(parents=True, exist_ok=True)
        blob = bc.encrypt(self.key, plaintext)
        path.write_bytes(blob)
        self.stats["new"] += 1
        self.stats["bytes"] += len(blob)
        return len(blob)


def build(work: Path, out: Path, password: str, new_salt: bool = False, iterations: int = bc.ITERATIONS):
    papers = load_papers(work)
    if not papers:
        raise SystemExit(f"No papers found in {work} (expected work/<paper-id>/questions.json). Nothing written.")

    old_meta = bc.read_meta(out / "meta.json")
    salt = None
    if (out / "meta.json").exists() and not new_salt:
        # An existing bank must keep its salt, otherwise every file is re-encrypted, the magic link changes and every friend's
        # saved key stops working. So a password that does not match is an error, not a reason to start a new bank silently.
        try:
            import base64
            old_salt = base64.b64decode(old_meta["salt"])
            matches = bc.key_matches_meta(bc.derive_key(password, old_salt, old_meta["iter"]), old_meta)
        except Exception:
            raise SystemExit(f"{out / 'meta.json'} exists but cannot be read. Refusing to overwrite the bank. "
                             "Restore the file from git, or pass --new-salt to deliberately start a new bank (new magic link).")
        if not matches:
            raise SystemExit("The password does not match the existing bank in " + str(out) + ". Nothing was written.\n"
                             "Check BANK_PASSWORD / .bank-password. To deliberately change the password (new salt, new magic link, "
                             "every friend must unlock again and ~100 MB is re-encrypted) run again with --new-salt.")
        salt = old_salt  # same password: keep the salt so file names stay stable
    if salt is None:
        salt = os.urandom(16)
    key = bc.derive_key(password, salt, iterations)

    writer = Writer(out, key)
    levels = {}
    report = {"papers": [], "excluded": [], "levels": {}}

    for pdir, data in papers:
        paper = data["paper"]
        level = int(paper["level"])
        lv = levels.setdefault(level, {"papers": [], "units": [], "media": {}})
        lv["papers"].append({"id": paper["id"], "title": paper.get("title", paper["id"]), "examVersion": paper.get("examVersion", "")})
        kept_q = excluded_q = 0

        def media(kind, item_id, rel):
            """Register a file and return its opaque name."""
            if not rel:
                return None
            src = pdir / rel
            if not src.is_file():
                raise SystemExit(f"{paper['id']}: missing file {rel}")
            name = bc.media_name(salt, kind, item_id)
            size = writer.put(f"hsk{level}/m/{name}.bin", src.read_bytes())
            lv["media"][name] = {"k": kind, "size": size}
            return name

        for unit in data["units"]:
            u = copy.deepcopy(unit)
            questions = []
            for q in u["questions"]:
                if q.get("exclude"):
                    excluded_q += 1
                    report["excluded"].append((q["id"], q["exclude"]))
                    continue
                q.pop("exclude", None)
                if q.get("audio"):
                    q["audio"] = media("audio", q["id"], q["audio"])
                if q.get("options"):
                    for o in q["options"]:
                        if o.get("image"):
                            o["image"] = media("image", f"{q['id']}:{o['key']}", o["image"])
                questions.append(q)
            if not questions:
                continue
            u["questions"] = questions
            ctx = u.setdefault("context", {})
            if ctx.get("audio"):
                ctx["audio"] = media("audio", u["id"], ctx["audio"])
            if ctx.get("image"):
                ctx["image"] = media("image", u["id"], ctx["image"])
            for o in ctx.get("sharedOptions") or []:
                if o.get("image"):
                    o["image"] = media("image", f"{u['id']}:{o['key']}", o["image"])
            u["paper"] = paper["id"]
            lv["units"].append(u)
            kept_q += len(questions)
        report["papers"].append((paper["id"], kept_q, excluded_q))

    for level, lv in sorted(levels.items()):
        index = {"v": bc.FORMAT_VERSION, "level": level, "papers": lv["papers"], "units": lv["units"], "media": lv["media"]}
        size = writer.put(f"hsk{level}/index.bin", json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        report["levels"][level] = {
            "units": len(lv["units"]),
            "questions": sum(len(u["questions"]) for u in lv["units"]),
            "index_bytes": size,
            "media_files": len(lv["media"]),
            "media_bytes": sum(m["size"] for m in lv["media"].values()),
        }

    # meta.json is plain; it holds nothing but the format, salt, iteration count, levels and the encrypted check value
    meta = bc.make_meta(key, salt, levels.keys(), iterations)
    if old_meta and old_meta.get("salt") == meta["salt"] and old_meta.get("levels") == meta["levels"] \
            and old_meta.get("iter") == iterations and bc.key_matches_meta(key, old_meta):
        meta = old_meta  # unchanged: don't rewrite
    (out / "meta.json").parent.mkdir(parents=True, exist_ok=True)
    (out / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    writer.written.add("meta.json")

    # delete outputs that are no longer referenced
    removed = 0
    for p in sorted(out.rglob("*"), reverse=True):
        if p.is_file() and p.relative_to(out).as_posix() not in writer.written:
            p.unlink()
            removed += 1
        elif p.is_dir() and not any(p.iterdir()):
            p.rmdir()
    report["removed"] = removed
    report["write"] = writer.stats
    report["key"] = key
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", type=Path, help="folder with <paper-id>/questions.json (default: <private>/work)")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "bank")
    ap.add_argument("--new-salt", action="store_true", help="deliberately start a new bank with a new salt (new magic link; old links and saved keys stop working). Needed when the password changes")
    ap.add_argument("--magic-link", action="store_true", help="print the #k=... part of the unlock link")
    args = ap.parse_args()
    private = private_dir()
    work = args.work or private / "work"
    r = build(work, args.out, get_password(private), new_salt=args.new_salt)
    print(f"Bank written to {args.out}")
    for pid, kept, excl in r["papers"]:
        print(f"  {pid}: {kept} questions" + (f", {excl} excluded" if excl else ""))
    for qid, why in r["excluded"]:
        print(f"    excluded {qid}: {why}")
    for level, s in r["levels"].items():
        print(f"  HSK {level}: {s['units']} units, {s['questions']} questions, index {s['index_bytes'] / 1024:.0f} KB, "
              f"{s['media_files']} media files {s['media_bytes'] / 1e6:.1f} MB")
    w = r["write"]
    print(f"  files: {w['new']} written ({w['bytes'] / 1e6:.1f} MB), {w['same']} unchanged, {r['removed']} removed")
    if args.magic_link:
        print("#k=" + bc.b64url(r["key"]))


if __name__ == "__main__":
    main()
