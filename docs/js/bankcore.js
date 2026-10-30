// Pure logic of the question bank (no DOM, no storage): grading, tab statistics, picking units for a set.
// Units and questions follow specs/mock-tests.md section 2.

export const TABS = [
  { id: "nghe", label: "Nghe" },
  { id: "doc", label: "Đọc" },
  { id: "sapxep", label: "Sắp xếp câu" },
];

// Filter chips per tab: [type id, label]
export const TYPE_CHIPS = {
  nghe: [["tf", "Đúng / Sai"], ["choice", "Chọn đáp án"]],
  doc: [["wordbank", "Chọn từ"], ["choice", "Đọc hiểu"]],
  sapxep: [["order-sentences", "Sắp xếp câu"], ["order-words", "Sắp xếp từ"]],
};

const PUNCT = /[\s。？！，、；：．.?!,;:"'“”‘’（）()[\]【】—…·《》]/g;

/** Ignore spaces and punctuation (the final 。 in particular) when comparing sentences. */
export function normSentence(s) {
  return String(s ?? "").replace(PUNCT, "");
}

/** Answer line of an ordering question: `picked` is an array of option indices in the order the learner chose. */
export function orderResponse(q, picked) {
  const opts = q.options || [];
  return { keys: picked.map((i) => opts[i].key).join(""), text: picked.map((i) => opts[i].text).join("") };
}

/** Is the response correct? `response`: a key / "✓" / "✗" for choice-like questions, or an array of picked indices for ordering. */
export function grade(unit, q, response) {
  if (unit.type === "order-sentences") return orderResponse(q, response).keys === q.answer;
  if (unit.type === "order-words") {
    const got = normSentence(orderResponse(q, response).text);
    return [q.answer, ...(q.alsoAccept || [])].some((a) => normSentence(a) === got);
  }
  return response === q.answer;
}

/** Text shown as "the correct answer" for an ordering question. */
export function correctOrderText(unit, q) {
  if (unit.type === "order-sentences") {
    const byKey = Object.fromEntries((q.options || []).map((o) => [o.key, o.text]));
    return [...q.answer].map((k) => `${k}. ${byKey[k] ?? ""}`).join("  →  ");
  }
  return q.answer;
}

/** `progress`: { [questionId]: { ok: 1|0, wrong: n } } */
export const isOk = (progress, id) => !!(progress[id] && progress[id].ok);
export const isWrong = (progress, id) => !!(progress[id] && !progress[id].ok && progress[id].wrong > 0);

export function tabStats(units, tab, progress) {
  let total = 0, ok = 0, wrong = 0;
  for (const u of units) {
    if (u.skill !== tab) continue;
    for (const q of u.questions) {
      total++;
      if (isOk(progress, q.id)) ok++;
      else if (isWrong(progress, q.id)) wrong++;
    }
  }
  return { total, ok, wrong, remaining: total - ok };
}

export function levelStats(units, progress) {
  let total = 0, ok = 0;
  for (const u of units) for (const q of u.questions) { total++; if (isOk(progress, q.id)) ok++; }
  return { total, ok };
}

/** Units that qualify for a set. mode "new": has a question not yet answered correctly. mode "wrong": has a question answered wrong and not yet right. */
export function candidateUnits(units, { tab, types = [], mode, progress }) {
  const want = mode === "wrong" ? (q) => isWrong(progress, q.id) : (q) => !isOk(progress, q.id);
  return units.filter((u) => u.skill === tab && (types.length === 0 || types.includes(u.type)) && u.questions.some(want));
}

/** Add whole units (in the given, already shuffled order) until `size` questions are reached. size 0 = all. */
export function takeUnits(candidates, size) {
  const out = [];
  let count = 0;
  for (const u of candidates) {
    if (size > 0 && count >= size) break;
    out.push(u);
    count += u.questions.length;
  }
  return out;
}

/** Progress update for an answer: returns the new entry, or null to delete it. Pure so it can be unit-tested. */
export function applyResult(entry, correct) {
  const wrong = entry?.wrong || 0;
  return correct ? { ok: 1, wrong } : { ok: 0, wrong: wrong + 1 };
}

/** "Câu của mình cũng đúng": undo the wrong mark that was just recorded and count the question as correct. */
export function applyOverride(entry) {
  return { ok: 1, wrong: Math.max(0, (entry?.wrong || 0) - 1) };
}
