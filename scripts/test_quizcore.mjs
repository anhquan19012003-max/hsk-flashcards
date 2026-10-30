// Unit test of the Trắc nghiệm generator (docs/js/quizcore.js) over ALL 4,545 words x every valid type, fixed seeds.
// Usage: node scripts/test_quizcore.mjs
import fs from "node:fs";
import { createQuiz, makeRng, TYPE_IDS, toneVariants, tonelessPinyin, meaningSegments, shortMeaning, blankSentence,
  applyResult, quizStats, candidateWords, eligibleWords, KEYS } from "../docs/js/quizcore.js";
import { canon } from "../docs/js/check.js";

let fails = 0;
const check = (name, ok, detail = "") => { if (!ok) fails++; console.log((ok ? "PASS " : "FAIL ") + name + (!ok && detail ? `  [${detail}]` : "")); };

const byLevel = {};
const all = [];
for (let n = 1; n <= 5; n++) {
  byLevel[n] = JSON.parse(fs.readFileSync(new URL(`../docs/data/hsk${n}.json`, import.meta.url))).words;
  all.push(...byLevel[n]);
}
const gen = createQuiz(byLevel);
const byId = new Map(all.map((w) => [w.id, w]));

// ---- small helpers
check("meaning segments split, lowercase, drop (parentheses)", JSON.stringify(meaningSegments("Yêu; Thích (nhiều), Mến")) === JSON.stringify(["yêu", "thích", "mến"]));
check("long meaning cut at the first ;", shortMeaning("a".repeat(30) + "; " + "b".repeat(30)) === "a".repeat(30) && shortMeaning("ngắn; gọn") === "ngắn; gọn");
check("toneless pinyin", tonelessPinyin("ānjìng") === "anjing" && tonelessPinyin("nǚ'ér") === "nuer");
const tv = toneVariants("ānjìng");
check("tone variants keep letters, change tones, never the original", tv.length > 3 && !tv.includes("ānjìng") && tv.every((v) => tonelessPinyin(v) === "anjing") && tv.includes("ànjìng") && tv.includes("ānjīng") && tv.includes("ánjìng"), tv.slice(0, 5).join());
check("tone marks stay on the same vowel", toneVariants("hǎo").every((v) => /^h[āáǎà]o$/.test(v)) && toneVariants("liú").every((v) => /^li[ūúǔù]$/.test(v)) && toneVariants("nǚ").every((v) => /^n[ǖǘǚǜ]$/.test(v)));
check("neutral-only pinyin has no variants", toneVariants("ba").length === 0);
check("blank sentence", blankSentence({ hanzi: "爱", example: { zh: "我爱我的家。" } }) === "我＿＿我的家。" && blankSentence({ hanzi: "有(一)些", example: { zh: "他有一些朋友。" } }) === null);
check("applyResult", JSON.stringify(applyResult(undefined, true)) === '{"ok":1,"wrong":0}' && JSON.stringify(applyResult({ ok: 1, wrong: 2 }, false)) === '{"ok":0,"wrong":3}' && JSON.stringify(applyResult({ ok: 0, wrong: 2 }, true)) === '{"ok":1,"wrong":2}');

// ---- every word x every valid type, over a few seeds
const SEEDS = [1, 20261030];
let made = 0, fallbacks = 0, impossible = [];
const typeCount = Object.fromEntries(TYPE_IDS.map((t) => [t, 0]));
const noType = Object.fromEntries(TYPE_IDS.map((t) => [t, 0]));
const fallbackByLevel = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
const problems = [];
const problem = (msg) => { if (problems.length < 15) problems.push(msg); problems.count = (problems.count || 0) + 1; };

for (const seed of SEEDS) {
  const rng = makeRng(seed);
  for (const w of all) {
    const valid = gen.validTypes(w);
    for (const t of TYPE_IDS) if (!valid.includes(t) && seed === SEEDS[0]) noType[t]++;
    for (const t of valid) {
      const q = gen.make(w, t, rng);
      if (!q) { if (seed === SEEDS[0]) impossible.push(`${w.id}:${t}`); continue; }
      made++;
      if (seed === SEEDS[0]) { typeCount[t]++; if (q.fallback) { fallbacks++; fallbackByLevel[q.level]++; } }
      const ctx = `${w.id} ${w.hanzi} ${t}`;
      // exactly 4 options, distinct as displayed, keys A-D, exactly one correct
      if (q.options.length !== 4) problem(`${ctx}: ${q.options.length} options`);
      const texts = q.options.map((o) => o.text.toLowerCase());
      if (new Set(texts).size !== 4 || texts.some((x) => !x)) problem(`${ctx}: duplicate/empty option text ${texts.join("|")}`);
      if (q.options.map((o) => o.key).join("") !== KEYS.join("")) problem(`${ctx}: keys`);
      const right = q.options.filter((o) => o.key === q.answer);
      if (right.length !== 1 || right[0].wid !== w.id) problem(`${ctx}: answer key`);
      const mine = new Set(meaningSegments(w.meaning));
      const myAccept = new Set(w.accept.map(canon));
      for (const o of q.options) {
        if (o.key === q.answer) continue;
        if (t === "pinyin" && !o.wid) { // tone variant
          if (myAccept.has(canon(o.text))) problem(`${ctx}: pinyin variant ${o.text} equals an accepted answer`);
          if (o.text === w.pinyin) problem(`${ctx}: pinyin variant equals the answer`);
          continue;
        }
        const c = byId.get(o.wid);
        if (!c) { problem(`${ctx}: option without a word`); continue; }
        if (c.hanzi === w.hanzi) problem(`${ctx}: wrong option has the same hanzi (${c.id})`);
        if (w.accept.includes(c.hanzi) || c.accept.includes(w.hanzi)) problem(`${ctx}: wrong option ${c.hanzi} is in the accept list`);
        if (meaningSegments(c.meaning).some((s) => mine.has(s))) problem(`${ctx}: wrong option ${c.hanzi} shares a meaning`);
        if (t === "nghe" && tonelessPinyin(c.pinyin) === tonelessPinyin(w.pinyin)) problem(`${ctx}: wrong option ${c.hanzi} sounds the same`);
        if (t === "pinyin" && myAccept.has(canon(c.pinyin))) problem(`${ctx}: pinyin option equals an accepted answer`);
        if (t === "hanviet" && c.hanviet.trim().toLowerCase() === w.hanviet.trim().toLowerCase()) problem(`${ctx}: hanviet option equals the answer`);
        if (t === "hanviet" && c.hanviet.trim().split(/\s+/).length !== w.hanviet.trim().split(/\s+/).length) problem(`${ctx}: hanviet syllable count differs`);
      }
      if (t === "nghia" && q.options.some((o) => o.text.length > 40 && o.text.includes(";"))) problem(`${ctx}: long meaning not cut at ;`);
    }
  }
}
check(`${made} questions generated: all satisfy the hard rules`, problems.count === undefined, problems.join("\n      "));
check("every valid word x type could be generated", impossible.length === 0, impossible.slice(0, 10).join(", "));
check("a word without example/hanviet never gets that type", gen.validTypes(byId.get("1-0445")).includes("dientu") === false && all.filter((w) => !w.hanviet).every((w) => !gen.validTypes(w).includes("hanviet")));
check("no voice -> nghe is never valid", all.slice(0, 50).every((w) => !gen.validTypes(w, { voice: false }).includes("nghe")));

// ---- determinism
const a1 = gen.make(all[100], "nghia", makeRng(7)), a2 = gen.make(all[100], "nghia", makeRng(7));
check("same seed -> same question", JSON.stringify(a1) === JSON.stringify(a2));

// ---- sets & stats
const lvl1 = byLevel[1];
const elig = eligibleWords(lvl1, { gen, pool: "all", types: ["hanviet"], learnedFn: () => false });
check("eligible words need a valid chosen type", elig.length === lvl1.filter((w) => gen.validTypes(w).includes("hanviet")).length);
check("pool 'learned' keeps only learned words", eligibleWords(lvl1, { gen, pool: "learned", learnedFn: (id) => id === "1-0001" }).map((w) => w.id).join() === "1-0001");
const quiz = { "1-0001": { ok: 1, wrong: 0 }, "1-0002": { ok: 0, wrong: 1 } };
const st = quizStats(lvl1, quiz);
check("stats", st.ok === 1 && st.wrong === 1 && st.remaining === lvl1.length - 1 && st.total === lvl1.length);
check("new = not answered correctly; wrong = wrong and not yet right", candidateWords(lvl1, "new", quiz).length === lvl1.length - 1 && candidateWords(lvl1, "wrong", quiz).map((w) => w.id).join() === "1-0002");

// ---- report
console.log("\nReport (seed 1):");
console.log("  questions per type:", JSON.stringify(typeCount));
console.log("  words that cannot get a type:", JSON.stringify(noType));
console.log(`  fallback to lower levels needed for ${fallbacks} of ${Object.values(typeCount).reduce((a, b) => a + b, 0)} questions; by level:`, JSON.stringify(fallbackByLevel));
console.log(fails ? `\n${fails} FAILED` : "\nquizcore: all passed");
process.exit(fails ? 1 : 0);
