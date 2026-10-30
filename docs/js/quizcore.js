// Trắc nghiệm (Phase 9, specs/vocab-quiz.md): pure logic of the vocab multiple-choice quiz. No DOM, no storage.
// The generator builds questions from the public word data (docs/data/hsk{N}.json) and can be unit-tested over all words.
import { canon } from "./check.js";

export const TYPES = [
  { id: "nghia", label: "Chọn nghĩa đúng" },
  { id: "chuhan", label: "Chọn chữ Hán đúng" },
  { id: "pinyin", label: "Chọn pinyin đúng" },
  { id: "nghe", label: "Nghe và chọn từ" },
  { id: "dientu", label: "Điền từ vào chỗ trống" },
  { id: "hanviet", label: "Chọn âm Hán Việt" },
];
export const TYPE_IDS = TYPES.map((t) => t.id);
export const KEYS = ["A", "B", "C", "D"];
export const BLANK = "＿＿";
const MAX_MEANING = 40;

// ---------- small helpers ----------
/** Seeded random generator (mulberry32) for repeatable tests. Returns a function giving numbers in [0, 1). */
export function makeRng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffled(list, rng = Math.random) {
  const a = list.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export const levelOf = (word) => Number(String(word.id).split("-")[0]);

/** Meaning segments used to detect "shares a meaning": split on , ; trim, lowercase, drop (parenthesised text). */
export function meaningSegments(meaning) {
  return String(meaning ?? "")
    .split(/[,;，；]/)
    .map((s) => s.replace(/\([^)]*\)|（[^）]*）/g, "").replace(/\s+/g, " ").trim().toLowerCase())
    .filter(Boolean);
}

/** Meaning text shown in an option: very long ones are cut at the first `;`. */
export function shortMeaning(meaning) {
  const m = String(meaning ?? "").trim();
  if (m.length <= MAX_MEANING) return m;
  const i = m.indexOf(";");
  return i > 0 ? m.slice(0, i).trim() : m;
}

/** Pinyin without tone marks (ü → u), letters only: used to tell whether two words sound the same when tones are ignored. */
export function tonelessPinyin(pinyin) {
  return canon(pinyin).normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z]/g, "");
}

const hanziChars = (hanzi) => [...String(hanzi).replace(/[()（）]/g, "")];

// ---------- tone variants of a pinyin string ----------
const TONE_ROWS = {
  a: "āáǎà", e: "ēéěè", i: "īíǐì", o: "ōóǒò", u: "ūúǔù", "ü": "ǖǘǚǜ",
};
const MARK_INFO = new Map(); // marked vowel -> [base vowel, tone index 0..3]
for (const [base, row] of Object.entries(TONE_ROWS)) [...row].forEach((ch, i) => MARK_INFO.set(ch, [base, i]));

/**
 * Wrong pinyin options built from tone variants of `pinyin`: change the tone of one or two marked syllables.
 * Returns distinct strings that differ from `pinyin` itself (the caller removes any that equal an accepted answer).
 * Neutral-tone syllables carry no mark, so words made only of those get no variants.
 */
export function toneVariants(pinyin) {
  const chars = [...String(pinyin).normalize("NFC")];
  const marked = [];
  chars.forEach((ch, i) => { if (MARK_INFO.has(ch)) marked.push(i); });
  const swap = (arr, i, tone) => { const [base] = MARK_INFO.get(chars[i]); arr[i] = TONE_ROWS[base][tone]; };
  const out = new Set();
  const make = (changes) => {
    const arr = chars.slice();
    for (const [i, tone] of changes) swap(arr, i, tone);
    const s = arr.join("");
    if (s !== pinyin) out.add(s);
  };
  const others = (i) => [0, 1, 2, 3].filter((t) => t !== MARK_INFO.get(chars[i])[1]);
  for (const i of marked) for (const t of others(i)) make([[i, t]]);
  for (let x = 0; x < marked.length; x++) {
    for (let y = x + 1; y < marked.length; y++) {
      for (const tx of others(marked[x])) for (const ty of others(marked[y])) make([[marked[x], tx], [marked[y], ty]]);
    }
  }
  return [...out];
}

// ---------- the generator ----------
/**
 * `wordsByLevel`: { 1: [word…], 2: [word…], … } (the content of docs/data/hsk{N}.json).
 * Returns an object with validTypes(word, {voice}) and make(word, type, rng).
 */
export function createQuiz(wordsByLevel) {
  const meta = new Map(); // word id -> precomputed facts
  const info = (w) => {
    let m = meta.get(w.id);
    if (!m) {
      const accept = new Set((w.accept || []).map(canon));
      accept.add(canon(w.hanzi));
      accept.add(canon(w.pinyin));
      const chars = hanziChars(w.hanzi);
      const hv = w.hanviet && !/\?/.test(w.hanviet) ? w.hanviet.trim().toLowerCase() : "";
      m = {
        segs: new Set(meaningSegments(w.meaning)),
        accept,
        acceptHanzi: new Set((w.accept || []).filter((a) => /[一-鿿]/.test(a))),
        chars,
        charSet: new Set(chars),
        len: chars.length,
        toneless: tonelessPinyin(w.pinyin),
        hv,
        hvSyl: hv ? hv.split(/\s+/) : [],
        hvSet: new Set(hv ? hv.split(/\s+/).map((s) => s.replace(/[()]/g, "")) : []),
      };
      meta.set(w.id, m);
    }
    return m;
  };

  /** Hard rule: may `c` appear as a WRONG option for `w`? */
  const compatible = (w, c) => {
    if (c.id === w.id || c.hanzi === w.hanzi) return false;
    const a = info(w), b = info(c);
    if (a.acceptHanzi.has(c.hanzi) || b.acceptHanzi.has(w.hanzi)) return false;
    for (const s of a.segs) if (b.segs.has(s)) return false;
    return true;
  };

  const needs = {
    nghia: () => true,
    chuhan: () => true,
    pinyin: () => true,
    nghe: (w, { voice }) => voice !== false,
    dientu: (w) => !!(w.example && w.example.zh && w.example.zh.includes(w.hanzi)),
    hanviet: (w) => !!info(w).hv,
  };

  function validTypes(word, { voice = true } = {}) {
    return TYPE_IDS.filter((t) => needs[t](word, { voice }));
  }

  // Candidate words for wrong options: same level first, then lower levels (only used when the level runs short).
  const levels = Object.keys(wordsByLevel).map(Number).sort((a, b) => a - b);
  const poolFor = (level, step) => {
    // step 0: the same level; step k>0: the level k below (if any)
    const l = level - step;
    return wordsByLevel[l] || [];
  };

  /** Soft-preference score of candidate `c` for target `w` (higher = more believable). */
  function score(type, w, c, rng) {
    const a = info(w), b = info(c);
    let s = rng() * 1.5;
    if (c.pos && c.pos === w.pos) s += 4;
    if (b.len === a.len) s += 2;
    if (type === "chuhan" || type === "nghe" || type === "dientu") {
      for (const ch of b.charSet) if (a.charSet.has(ch)) { s += 3; break; }
    }
    if (type === "hanviet") {
      for (const syl of b.hvSet) if (a.hvSet.has(syl)) { s += 5; break; }
    }
    if (type === "dientu" && w.example.zh.includes(c.hanzi)) s -= 6; // would already be in the sentence
    return s;
  }

  /** Text of `c` as an option of this type, or "" when `c` cannot be used (never equal to `target`'s text). */
  function optionText(type, w, c) {
    const a = info(w), b = info(c);
    switch (type) {
      case "nghia": return shortMeaning(c.meaning);
      case "chuhan": case "dientu": return c.hanzi;
      case "nghe": return b.toneless === a.toneless ? "" : c.hanzi;
      case "pinyin": return b.len !== a.len || a.accept.has(canon(c.pinyin)) ? "" : c.pinyin; // same syllable count, never an accepted answer
      case "hanviet":
        if (!b.hv || b.hvSyl.length !== a.hvSyl.length || b.hv === a.hv) return "";
        return c.hanviet.trim();
      default: return "";
    }
  }

  const correctText = (type, w) => {
    switch (type) {
      case "nghia": return shortMeaning(w.meaning);
      case "chuhan": case "nghe": case "dientu": return w.hanzi;
      case "pinyin": return w.pinyin;
      default: return w.hanviet.trim();
    }
  };

  /** Build one question, or null when this word cannot get this type. */
  function make(word, type, rng = Math.random, { voice = true } = {}) {
    if (!needs[type] || !needs[type](word, { voice })) return null;
    const right = correctText(type, word);
    const shown = new Set([right.toLowerCase()]);
    const wrong = [];
    let fallback = false;
    const take = (text, wid) => {
      const key = text.toLowerCase();
      if (!text || shown.has(key) || wrong.length >= 3) return false;
      shown.add(key);
      wrong.push({ text, wid: wid || null });
      return true;
    };

    if (type === "pinyin") {
      const a = info(word);
      const variants = shuffled(toneVariants(word.pinyin).filter((v) => !a.accept.has(canon(v))), rng);
      // prefer a mix: first the single-syllable changes, then the rest (they were generated in that order before shuffling)
      for (const v of variants) if (wrong.length < 3) take(v, null);
    }

    for (let step = 0; wrong.length < 3 && level(word) - step >= 1; step++) {
      const pool = poolFor(level(word), step);
      const scored = [];
      for (const c of pool) {
        if (!compatible(word, c)) continue;
        const text = optionText(type, word, c);
        if (!text) continue;
        scored.push([score(type, word, c, rng), text, c.id]);
      }
      scored.sort((x, y) => y[0] - x[0]);
      for (const [, text, id] of scored) take(text, id);
      if (wrong.length < 3 && step === 0) fallback = true;
    }
    if (wrong.length < 3) return null;

    const all = shuffled([{ text: right, wid: word.id, right: true }, ...wrong], rng);
    const options = all.map((o, i) => ({ key: KEYS[i], text: o.text, wid: o.wid }));
    const answer = options[all.findIndex((o) => o.right)].key;
    return { id: `${word.id}:${type}`, wordId: word.id, type, level: level(word), options, answer, fallback };
  }

  const level = levelOf;
  return { validTypes, make, levels, info };
}

/** The example sentence with the word replaced by ＿＿ (null when the sentence does not contain it exactly). */
export function blankSentence(word) {
  const zh = word.example && word.example.zh;
  if (!zh || !word.hanzi || !zh.includes(word.hanzi)) return null;
  return zh.replace(word.hanzi, BLANK);
}

// ---------- progress & sets (storage is injected by the UI) ----------
/** `quiz`: { [wordId]: { ok: 1|0, wrong: n } } */
export const isOk = (quiz, id) => !!(quiz[id] && quiz[id].ok);
export const isWrong = (quiz, id) => !!(quiz[id] && !quiz[id].ok && quiz[id].wrong > 0);

/** Quiz progress after an answer. */
export function applyResult(entry, correct) {
  const wrong = entry?.wrong || 0;
  return correct ? { ok: 1, wrong } : { ok: 0, wrong: wrong + 1 };
}

/**
 * Words that can be quizzed: in the chosen pool ("all" | "learned") and with at least one chosen, valid type.
 * `learnedFn(id)`: is the word learned in any flashcard direction?
 */
export function eligibleWords(words, { gen, pool = "all", types = TYPE_IDS, learnedFn = () => true, voice = true }) {
  return words.filter((w) => (pool === "all" || learnedFn(w.id)) && gen.validTypes(w, { voice }).some((t) => types.includes(t)));
}

export function quizStats(words, quiz) {
  let ok = 0, wrong = 0;
  for (const w of words) {
    if (isOk(quiz, w.id)) ok++;
    else if (isWrong(quiz, w.id)) wrong++;
  }
  return { total: words.length, ok, wrong, remaining: words.length - ok };
}

/** Words for a set. mode "new": not yet answered correctly. mode "wrong": answered wrong and not yet right. */
export function candidateWords(eligible, mode, quiz) {
  return eligible.filter((w) => (mode === "wrong" ? isWrong(quiz, w.id) : !isOk(quiz, w.id)));
}

/** Pick one of the chosen types, valid for this word, at random. */
export function pickType(word, types, gen, rng = Math.random, voice = true) {
  const valid = gen.validTypes(word, { voice }).filter((t) => types.includes(t));
  return valid.length ? valid[Math.floor(rng() * valid.length)] : null;
}
