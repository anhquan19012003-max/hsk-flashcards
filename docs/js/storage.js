// Progress + settings in localStorage. Every access is wrapped in try/catch; when storage is
// unavailable (private mode, blocked) the app keeps working with in-memory state for the session.
const PROGRESS_KEY = "hskfc.v1.progress";
const SETTINGS_KEY = "hskfc.v1.settings";
const BANK_KEY = "hskfc.v1.bank";
const QUIZ_KEY = "hskfc.v1.quiz";

export const DEFAULT_SETTINGS = { sessionSize: 20, speed: "normal", voice: "", writingOutline: false, writingPinyin: true, bankSize: 10,
  quizTypes: ["nghia", "chuhan", "pinyin", "nghe", "dientu", "hanviet"], quizPool: "all", quizSize: 20 };

function read(key) {
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const value = JSON.parse(raw);
      if (value && typeof value === "object" && !Array.isArray(value)) return value;
    }
  } catch (e) { /* storage unavailable or corrupt: start empty */ }
  return {};
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    return false;
  }
}

let progress = read(PROGRESS_KEY);
let settings = { ...DEFAULT_SETTINGS, ...read(SETTINGS_KEY) };
let bank = read(BANK_KEY); // question bank (Phase 8): { "<question id>": { ok: 1|0, wrong: n } }
let quiz = read(QUIZ_KEY); // Trắc nghiệm (Phase 9): { "<word id>": { ok: 1|0, wrong: n } }, per word, not per question type

const save = () => write(PROGRESS_KEY, progress);

export function isLearned(id, dir) {
  return !!(progress[id] && progress[id][dir]);
}

// Directions: zv (Trung → Việt), vz (Việt → Trung), wr (Luyện viết). `wr` is only stored when it is 1, so entries
// written before writing practice existed (and backups made then) stay valid and unchanged.
export function setLearned(id, dir, value) {
  const entry = progress[id] || { zv: 0, vz: 0 };
  if (dir === "wr") {
    if (value) entry.wr = 1;
    else delete entry.wr;
  } else {
    entry[dir] = value ? 1 : 0;
  }
  if (entry.zv || entry.vz || entry.wr) progress[id] = entry;
  else delete progress[id];
  return save();
}

/** Counts per direction (and "any") for ids of one level. `words` is optional and limits the count to real ids. */
export function levelStats(level, words) {
  const stats = { zv: 0, vz: 0, wr: 0, any: 0 };
  const valid = words ? new Set(words.map((w) => w.id)) : null;
  const prefix = level + "-";
  for (const id of Object.keys(progress)) {
    if (!id.startsWith(prefix) || (valid && !valid.has(id))) continue;
    const e = progress[id];
    if (e.zv) stats.zv++;
    if (e.vz) stats.vz++;
    if (e.wr) stats.wr++;
    if (e.zv || e.vz || e.wr) stats.any++;
  }
  return stats;
}

export function resetLevel(level) {
  const prefix = level + "-";
  for (const id of Object.keys(progress)) if (id.startsWith(prefix)) delete progress[id];
  return save();
}

// ---- question bank progress (Luyện đề) ----
const saveBank = () => write(BANK_KEY, bank);

export const getBank = () => bank;

export function setBankEntry(id, entry) {
  if (entry) bank[id] = entry;
  else delete bank[id];
  return saveBank();
}

export function resetBankIds(ids) {
  for (const id of ids) delete bank[id];
  return saveBank();
}

// ---- Trắc nghiệm progress (Phase 9) ----
const saveQuiz = () => write(QUIZ_KEY, quiz);

export const getQuiz = () => quiz;

export function setQuizEntry(id, entry) {
  if (entry) quiz[id] = entry;
  else delete quiz[id];
  return saveQuiz();
}

/** Forget the quiz progress of one level (ids start with "<level>-"). */
export function resetQuizLevel(level) {
  const prefix = level + "-";
  for (const id of Object.keys(quiz)) if (id.startsWith(prefix)) delete quiz[id];
  return saveQuiz();
}

export function exportProgress() {
  // The bank and the quiz travel in the same file under extra keys; each is left out while empty so older backups look the same.
  const out = { ...progress };
  if (Object.keys(bank).length) out._bank = bank;
  if (Object.keys(quiz).length) out._quiz = quiz;
  return JSON.stringify(out, null, 1);
}

/** Replace progress with an uploaded backup. Throws on an invalid file. Returns the number of words. */
export function importProgress(text) {
  const data = JSON.parse(text);
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("bad shape");
  const clean = {};
  let cleanBank = null;
  let cleanQuiz = null;
  for (const [id, e] of Object.entries(data)) {
    if (id === "_bank") { cleanBank = cleanBankProgress(e); continue; }
    if (id === "_quiz") { cleanQuiz = cleanQuizProgress(e); continue; }
    if (!/^[1-5]-\d{4}$/.test(id) || !e || typeof e !== "object") throw new Error("bad entry " + id);
    const zv = e.zv ? 1 : 0;
    const vz = e.vz ? 1 : 0;
    const wr = e.wr ? 1 : 0;
    if (zv || vz || wr) clean[id] = wr ? { zv, vz, wr } : { zv, vz };
  }
  progress = clean;
  save();
  if (cleanBank) { // old backups have no bank part: the bank progress on this device is then left alone
    bank = cleanBank;
    saveBank();
  }
  if (cleanQuiz) { // same for the quiz part
    quiz = cleanQuiz;
    saveQuiz();
  }
  return Object.keys(clean).length;
}

function cleanBankProgress(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("bad bank");
  const clean = {};
  for (const [id, e] of Object.entries(data)) {
    if (!/^[\w-]{1,80}$/.test(id) || !e || typeof e !== "object") throw new Error("bad bank entry " + id);
    clean[id] = { ok: e.ok ? 1 : 0, wrong: Math.max(0, Math.min(999, Math.floor(Number(e.wrong)) || 0)) };
  }
  return clean;
}

function cleanQuizProgress(data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("bad quiz");
  const clean = {};
  for (const [id, e] of Object.entries(data)) {
    if (!/^[1-5]-\d{4}$/.test(id) || !e || typeof e !== "object") throw new Error("bad quiz entry " + id);
    clean[id] = { ok: e.ok ? 1 : 0, wrong: Math.max(0, Math.min(999, Math.floor(Number(e.wrong)) || 0)) };
  }
  return clean;
}

export const quizCountInBackup = (text) => Object.keys(JSON.parse(text)._quiz || {}).length;

export const bankCountInBackup = (text) => Object.keys(JSON.parse(text)._bank || {}).length;

export const getSettings = () => settings;

export function updateSettings(patch) {
  settings = { ...settings, ...patch };
  write(SETTINGS_KEY, settings);
  return settings;
}
