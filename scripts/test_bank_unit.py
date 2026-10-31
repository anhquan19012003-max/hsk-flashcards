"""Unit tests for the bank build side: crypto, validate_paper, build_bank, plaintext guard. No browser needed.

Usage: python scripts/test_bank_unit.py
"""
import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "bank"))
import bankcrypto as bc  # noqa: E402
import build_bank  # noqa: E402
import guard  # noqa: E402
import validate_paper as vp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIX_PAPER = ROOT / "scripts" / "fixtures" / "papers" / "hsk4-fixture-1"
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def fixture():
    return json.loads((FIX_PAPER / "questions.json").read_text(encoding="utf-8"))


def errors_of(data):
    return vp.validate(data, FIX_PAPER)[0]


def find(data, qid):
    for u in data["units"]:
        for q in u["questions"]:
            if q["id"] == qid:
                return u, q


def test_crypto():
    salt = b"s" * 16
    key = bc.derive_key("pw", salt, 1000)
    blob = bc.encrypt(key, "你好 hello".encode())
    check("crypto round trip", bc.decrypt(key, blob) == "你好 hello".encode() and blob[:4] == bc.MAGIC)
    check("two encryptions of the same data differ (random IV)", bc.encrypt(key, b"x") != bc.encrypt(key, b"x"))
    bad = False
    try:
        bc.decrypt(bc.derive_key("other", salt, 1000), blob)
    except Exception:
        bad = True
    check("wrong key is rejected", bad)
    tampered = bytearray(blob)
    tampered[-1] ^= 1
    try:
        bc.decrypt(key, bytes(tampered))
        ok = False
    except Exception:
        ok = True
    check("tampered file is rejected", ok)
    check("media names are opaque and depend on the salt",
          bc.media_name(salt, "audio", "q1") != bc.media_name(b"t" * 16, "audio", "q1") and len(bc.media_name(salt, "audio", "q1")) == 32)


def test_validate():
    data = fixture()
    check("fixture paper validates", errors_of(data) == [], str(errors_of(data)))

    def broken(mutate, expect, label):
        d = copy.deepcopy(data)
        mutate(d)
        errs = errors_of(d)
        check(f"validate catches: {label}", any(expect in e for e in errs), str(errs[:3]))

    broken(lambda d: find(d, "hsk4-fixture-1-3")[1].update(answer="Z"), "not one of the options", "answer not an option")
    broken(lambda d: find(d, "hsk4-fixture-1-1")[1].update(answer="A"), "tf answer", "tf answer not ✓/✗")
    broken(lambda d: find(d, "hsk4-fixture-1-3")[1].update(audio="clips/missing.mp3"), "file not found", "missing audio file")
    broken(lambda d: find(d, "hsk4-fixture-1-13")[1].update(answer="AAB"), "permutation", "order-sentences not a permutation")
    broken(lambda d: find(d, "hsk4-fixture-1-15")[1].update(answer="我喜欢吃香蕉。"), "exactly the given tiles", "order-words with other tiles")
    broken(lambda d: find(d, "hsk4-fixture-1-16")[1].update(alsoAccept=["我们明天去公园啊。"]), "exactly the given tiles", "bad alsoAccept")
    broken(lambda d: find(d, "hsk4-fixture-1-6")[0]["context"].pop("sharedOptions"), "no sharedOptions", "wordbank without shared options")
    broken(lambda d: find(d, "hsk4-fixture-1-3")[1].update(audio=None), "no audio clip", "listening question without audio")
    broken(lambda d: find(d, "hsk4-fixture-1-5")[1].update(id="hsk4-fixture-1-9"), "duplicate question id", "duplicate id")
    broken(lambda d: find(d, "hsk4-fixture-1-5")[1].update(id="hsk4-fixture-1-7"), "consecutive", "non-consecutive numbering in a unit")
    broken(lambda d: find(d, "hsk4-fixture-1-3")[0].update(type="nope"), "unknown type", "unknown type")
    broken(lambda d: find(d, "hsk4-fixture-1-6")[0].update(skill="nghe"), "cannot be in tab", "type in the wrong tab")
    d = copy.deepcopy(data)
    find(d, "hsk4-fixture-1-3")[1].update(audio=None, exclude="clip unclear")
    check("an excluded question needs no audio", not any("no audio" in e for e in errors_of(d)))
    # a real-format paper with a numbering profile: only 2 questions -> everything else is missing
    d = copy.deepcopy(data)
    d["paper"]["examVersion"] = "HSK 2.0"
    errs = errors_of(d)
    check("numbering profile: missing question numbers reported", any("missing question numbers" in e for e in errs))
    check("normalisation ignores spaces and final punctuation", vp.can_form("明天 我们去公园。", ["明天", "我们", "去公园"]))


def make_work(tmp: Path, extra_excluded=False):
    work = tmp / "work"
    shutil.copytree(FIX_PAPER, work / "hsk4-fixture-1")
    if extra_excluded:
        p = work / "hsk4-fixture-1" / "questions.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        find(d, "hsk4-fixture-1-2")[1]["exclude"] = "clip starts late"
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return work


def test_build_and_guard():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        work, out = make_work(tmp), tmp / "bank"
        r = build_bank.build(work, out, "pw-one", iterations=2000)
        files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
        check("build writes meta.json, one index per level, one file per clip/image",
              "meta.json" in files and "hsk4/index.bin" in files and sum(f.startswith("hsk4/m/") for f in files) == r["levels"][4]["media_files"] == 7, str(files))
        meta = json.loads((out / "meta.json").read_text())
        check("meta.json holds nothing but format, salt, iterations, levels, check", set(meta) == {"v", "salt", "iter", "levels", "check"} and meta["levels"] == [4])
        check("guard passes on a real encrypted bank", guard.check_bank(out) == [], str(guard.check_bank(out)))
        index = json.loads(bc.decrypt(r["key"], (out / "hsk4/index.bin").read_bytes()))
        check("index decrypts and holds all units", len(index["units"]) == 12 and all(len(n) == 32 for n in index["media"]))
        check("clip paths are replaced by opaque names", "clips/" not in json.dumps(index) and "img/" not in json.dumps(index))

        before = {f: (out / f).read_bytes() for f in files}
        build_bank.build(work, out, "pw-one", iterations=2000)
        same = all((out / f).read_bytes() == before[f] for f in files)
        check("rebuild with the same password changes no file (same salt, unchanged files kept)", same)

        # a different password must NOT silently start a new bank (new salt = new magic link, every saved key breaks)
        snapshot = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob("*") if p.is_file()}
        try:
            build_bank.build(work, out, "pw-two", iterations=2000)
            refused_pw = False
        except SystemExit as e:
            refused_pw = "does not match" in str(e) and "--new-salt" in str(e) and "pw-two" not in str(e) and "pw-one" not in str(e)
        after = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob("*") if p.is_file()}
        check("a different password is refused with a clear message and writes/deletes nothing", refused_pw and after == snapshot)

        (out / "meta.json").write_text("{ not json", encoding="utf-8")
        try:
            build_bank.build(work, out, "pw-one", iterations=2000)
            refused_bad = False
        except SystemExit as e:
            refused_bad = "cannot be read" in str(e)
        check("an unreadable meta.json is refused, not overwritten", refused_bad and (out / "meta.json").read_text() == "{ not json")
        (out / "meta.json").write_bytes(snapshot["meta.json"])

        build_bank.build(work, out, "pw-two", iterations=2000, new_salt=True)
        meta2 = json.loads((out / "meta.json").read_text())
        check("--new-salt (deliberate password change) -> new salt, all names change, old files removed",
              meta2["salt"] != meta["salt"] and not (set(files) - {"meta.json", "hsk4/index.bin"}) & {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()},
              "")

        work2 = make_work(tmp / "ex", extra_excluded=True)
        r2 = build_bank.build(work2, tmp / "bank2", "pw", iterations=2000)
        check("excluded questions are dropped and reported", r2["levels"][4]["questions"] == 15 and r2["excluded"] == [("hsk4-fixture-1-2", "clip starts late")], str(r2["excluded"]))

        try:
            build_bank.build(tmp / "nothing", tmp / "bank3", "pw")
            refused = False
        except SystemExit:
            refused = True
        check("build refuses to run (and wipe the bank) when there are no papers", refused and not (tmp / "bank3").exists())

        # ---- guard against planted plaintext
        def planted(name, data, expect):
            d = tmp / ("g-" + name)
            shutil.copytree(out, d)
            f = d / "hsk4" / "m" / name
            f.write_bytes(data)
            problems = guard.check_bank(d)
            check(f"guard catches {expect}", any(expect in p for p in problems), str(problems))

        planted("a.bin", json.dumps({"q": "题目"}, ensure_ascii=False).encode(), "magic header")
        planted("c.bin", b"ID3\x04\x00" + b"\x00" * 60, "starts like MP3")
        planted("d.bin", b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 60, "starts like")
        planted("e.bin", bc.MAGIC + b"\x01" * 12 + "这是一个没有加密的题目内容".encode() + b"\x01" * 20, "CJK")
        planted("f.txt", b"hello", "only .bin files")
        planted("g.bin", bc.MAGIC + b"\x00" * 5000, "entropy")
        d = tmp / "g-meta"
        shutil.copytree(out, d)
        m = json.loads((d / "meta.json").read_text())
        m["titles"] = ["Đề 1"]
        (d / "meta.json").write_text(json.dumps(m))
        check("guard catches extra keys in meta.json", any("unexpected keys" in p for p in guard.check_bank(d)))
        d = tmp / "g-json"
        shutil.copytree(out, d)
        (d / "hsk4" / "index.bin").write_text(json.dumps({"units": []}))
        check("guard catches a plain JSON index", any("hsk4/index.bin" in p for p in guard.check_bank(d)))

        # no false alarms on lots of random ciphertext-like data (this is what real files look like)
        big = tmp / "big"
        (big / "hsk4" / "m").mkdir(parents=True)
        for i in range(300):
            (big / "hsk4" / "m" / f"{i:032x}.bin").write_bytes(bc.MAGIC + os.urandom(12) + os.urandom(60000))
        (big / "meta.json").write_text((out / "meta.json").read_text())
        check("guard: no false alarms on 300 random 60 KB files", guard.check_bank(big) == [], str(guard.check_bank(big)[:3]))
        check("guard: a missing docs/bank is fine", guard.check_bank(tmp / "nope") == [])


def main():
    test_crypto()
    test_validate()
    test_build_and_guard()
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
