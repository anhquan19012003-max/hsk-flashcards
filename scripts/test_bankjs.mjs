// Browser-side bank logic in Node: decrypts the Python-built fixture with docs/js/bankcrypto.js, and tests bankcore.js.
// Usage: node scripts/test_bankjs.mjs
import { readFileSync } from "node:fs";
import { pbkdf2Sync } from "node:crypto";
import { decryptBlob, keyFromPassword, keyFromRaw, keyMatches, b64ToBytes } from "../docs/js/bankcrypto.js";
import * as core from "../docs/js/bankcore.js";

const bank = new URL("./fixtures/bank/", import.meta.url);
const read = (p) => readFileSync(new URL(p, bank));
const meta = JSON.parse(read("meta.json"));
let failed = 0;
const check = (name, ok) => { console.log((ok ? "PASS " : "FAIL ") + name); if (!ok) failed++; };

// ---- crypto: Python encrypts, the browser code decrypts
const key = await keyFromPassword("test-password", meta);
check("password -> key matches meta.check", await keyMatches(key, meta));
check("wrong password does not match", !(await keyMatches(await keyFromPassword("nope", meta), meta)));
const index = JSON.parse(new TextDecoder().decode(await decryptBlob(key, read("hsk4/index.bin"))));
check("index.bin decrypts to the fixture units", index.level === 4 && index.units.length === 12);
const names = Object.keys(index.media);
const clip = new Uint8Array(await decryptBlob(key, read(`hsk4/m/${names.find((n) => index.media[n].k === "audio")}.bin`)));
check("a clip decrypts to an MP3", (clip[0] === 0x49 && clip[1] === 0x44) || clip[0] === 0xff);
const img = new Uint8Array(await decryptBlob(key, read(`hsk4/m/${names.find((n) => index.media[n].k === "image")}.bin`)));
check("an image decrypts to WebP", String.fromCharCode(...img.slice(0, 4)) === "RIFF");
check("media size in the index equals the file size", names.every((n) => read(`hsk4/m/${n}.bin`).length === index.media[n].size));
// magic link: the raw derived key (as base64url) unlocks too
const raw = pbkdf2Sync("test-password", b64ToBytes(meta.salt), meta.iter, 32, "sha256");
const link = Buffer.from(raw).toString("base64url");
check("magic-link key unlocks", await keyMatches(await keyFromRaw(link), meta));
let threw = false;
try { await keyFromRaw("AAAA"); } catch (e) { threw = true; }
check("a link of the wrong length is rejected", threw);

// ---- grading
const unitOf = (id) => index.units.find((u) => u.questions.some((q) => q.id === id));
const q = (id) => unitOf(id).questions.find((x) => x.id === id);
const U = (id) => unitOf(id);
check("choice: right key", core.grade(U("hsk4-fixture-1-3"), q("hsk4-fixture-1-3"), "B") && !core.grade(U("hsk4-fixture-1-3"), q("hsk4-fixture-1-3"), "A"));
check("tf", core.grade(U("hsk4-fixture-1-1"), q("hsk4-fixture-1-1"), "✓") && !core.grade(U("hsk4-fixture-1-1"), q("hsk4-fixture-1-1"), "✗"));
const sent = q("hsk4-fixture-1-13"); // answer BAC
const idx = (k) => sent.options.findIndex((o) => o.key === k);
check("order-sentences: BAC right, ABC wrong", core.grade(U(sent.id), sent, [idx("B"), idx("A"), idx("C")]) && !core.grade(U(sent.id), sent, [idx("A"), idx("B"), idx("C")]));
const words = q("hsk4-fixture-1-16"); // 明天 我们 去公园 + alsoAccept 我们明天去公园。
check("order-words: main answer", core.grade(U(words.id), words, [0, 1, 2]));
check("order-words: alsoAccept", core.grade(U(words.id), words, [1, 0, 2]));
check("order-words: wrong order", !core.grade(U(words.id), words, [2, 1, 0]));
check("normSentence ignores spaces and final punctuation", core.normSentence("我 喜欢 吃苹果。") === core.normSentence("我喜欢吃苹果"));
check("correct order text for order-sentences lists A/B/C", core.correctOrderText(U(sent.id), sent).startsWith("B."));

// ---- progress, tabs, picking units
const progress = { "hsk4-fixture-1-1": { ok: 1, wrong: 0 }, "hsk4-fixture-1-2": { ok: 0, wrong: 2 } };
const st = core.tabStats(index.units, "nghe", progress);
check("tabStats: 5 questions, 1 ok, 1 wrong, 4 remaining", st.total === 5 && st.ok === 1 && st.wrong === 1 && st.remaining === 4);
const fresh = core.candidateUnits(index.units, { tab: "nghe", mode: "new", progress });
check("'new' pool skips fully-correct units, keeps wrong ones", !fresh.some((u) => u.id.endsWith("N1")) && fresh.some((u) => u.id.endsWith("N2")));
const wrong = core.candidateUnits(index.units, { tab: "nghe", mode: "wrong", progress });
check("'wrong' pool is only the wrong ones", wrong.length === 1 && wrong[0].id.endsWith("N2"));
const typed = core.candidateUnits(index.units, { tab: "doc", types: ["wordbank"], mode: "new", progress: {} });
check("type filter", typed.length === 1 && typed[0].type === "wordbank");
const taken = core.takeUnits(index.units.filter((u) => u.skill === "doc"), 3);
check("takeUnits adds whole units until the size is reached", taken.reduce((n, u) => n + u.questions.length, 0) >= 3 && taken.length === 1);
check("takeUnits size 0 = all", core.takeUnits(index.units, 0).length === index.units.length);
check("applyResult", JSON.stringify(core.applyResult(undefined, true)) === '{"ok":1,"wrong":0}' && JSON.stringify(core.applyResult({ ok: 0, wrong: 1 }, false)) === '{"ok":0,"wrong":2}');
check("applyOverride undoes the wrong mark", JSON.stringify(core.applyOverride({ ok: 0, wrong: 1 })) === '{"ok":1,"wrong":0}');

console.log(failed ? `bank js: ${failed} FAILED` : "bank js: all passed");
process.exit(failed ? 1 : 0);
