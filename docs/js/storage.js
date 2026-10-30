// Progress + settings in localStorage. Every access is wrapped in try/catch; when storage is
// unavailable (private mode, blocked) the app keeps working with in-memory state for the session.
const PROGRESS_KEY = "hskfc.v1.progress";
const SETTINGS_KEY = "hskfc.v1.settings";

export const DEFAULT_SETTINGS = { sessionSize: 20, speed: "normal", voice: "", writingOutline: false, writingPinyin: true };

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

export function exportProgress() {
  return JSON.stringify(progress, null, 1);
}

/** Replace progress with an uploaded backup. Throws on an invalid file. Returns the number of words. */
export function importProgress(text) {
  const data = JSON.parse(text);
  if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error("bad shape");
  const clean = {};
  for (const [id, e] of Object.entries(data)) {
    if (!/^[1-5]-\d{4}$/.test(id) || !e || typeof e !== "object") throw new Error("bad entry " + id);
    const zv = e.zv ? 1 : 0;
    const vz = e.vz ? 1 : 0;
    const wr = e.wr ? 1 : 0;
    if (zv || vz || wr) clean[id] = wr ? { zv, vz, wr } : { zv, vz };
  }
  progress = clean;
  save();
  return Object.keys(clean).length;
}

export const getSettings = () => settings;

export function updateSettings(patch) {
  settings = { ...settings, ...patch };
  write(SETTINGS_KEY, settings);
  return settings;
}
