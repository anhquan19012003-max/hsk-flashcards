// Answer checking for Việt → Trung, following the rules of the original Excel file:
// - any entry in `accept` (hanzi or pinyin) is a correct answer
// - case, spaces, apostrophes, "·", "-" and parentheses are ignored
// - ü may be typed as ü, v or u
// - pinyin with tone marks must have the right tones; pinyin without tones only checks the letters
// - tone numbers (ai4hao4) are converted to tone marks before comparing

const TONE_MARKS = {
  a: ["ā", "á", "ǎ", "à"], e: ["ē", "é", "ě", "è"], i: ["ī", "í", "ǐ", "ì"],
  o: ["ō", "ó", "ǒ", "ò"], u: ["ū", "ú", "ǔ", "ù"], "ü": ["ǖ", "ǘ", "ǚ", "ǜ"],
};
const FOLD_U = { "ǖ": "ū", "ǘ": "ú", "ǚ": "ǔ", "ǜ": "ù", "ü": "u", v: "u" };
const HAS_TONE = /[āáǎàēéěèīíǐìōóǒòūúǔù]/;

function applyToneNumbers(s) {
  return s.replace(/([a-züv]+)([1-5])/g, (m, syl, t) => {
    syl = syl.replace(/v/g, "ü");
    if (t === "5") return syl;
    let idx = syl.search(/[ae]/);
    if (idx < 0) {
      idx = syl.indexOf("ou");
      if (idx < 0) {
        for (let i = syl.length - 1; i >= 0; i--) {
          if ("aeiouü".includes(syl[i])) { idx = i; break; }
        }
      }
    }
    if (idx < 0) return syl;
    return syl.slice(0, idx) + TONE_MARKS[syl[idx]][Number(t) - 1] + syl.slice(idx + 1);
  });
}

/** Canonical form used for comparison. */
export function canon(input) {
  let s = String(input).normalize("NFC").toLowerCase();
  s = s.replace(/[\s'’‘`´·\-–—()（）]/g, "");
  s = applyToneNumbers(s);
  return s.replace(/[ǖǘǚǜüv]/g, (c) => FOLD_U[c]);
}

function toneless(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "");
}

function variants(entry) {
  const list = [entry];
  const noOptional = entry.replace(/[(（][^)）]*[)）]/g, "");
  if (noOptional && noOptional !== entry) list.push(noOptional);
  return list;
}

export function checkAnswer(input, accept) {
  const typed = canon(input);
  if (!typed) return false;
  const entries = accept.flatMap(variants).map(canon);
  if (entries.includes(typed)) return true;
  // pinyin typed without tone marks/numbers: compare letters only
  if (/^[a-z]+$/.test(typed) && !HAS_TONE.test(typed)) {
    return entries.some((e) => toneless(e) === typed);
  }
  return false;
}
