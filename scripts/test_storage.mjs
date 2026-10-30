// Unit tests for docs/js/storage.js (progress directions zv / vz / wr). Run: node scripts/test_storage.mjs
let fail = 0;
const eq = (name, got, want) => {
  if (JSON.stringify(got) !== JSON.stringify(want)) { fail++; console.log("FAIL", name, "got", JSON.stringify(got), "want", JSON.stringify(want)); }
};

// minimal localStorage so the module can run under Node
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => mem.set(k, String(v)),
  removeItem: (k) => mem.delete(k),
};
// an old progress file written before writing practice existed
mem.set("hskfc.v1.progress", JSON.stringify({ "1-0001": { zv: 1, vz: 0 }, "1-0002": { zv: 0, vz: 1 } }));

const store = await import("../docs/js/storage.js");
const saved = () => JSON.parse(mem.get("hskfc.v1.progress"));

eq("old entry readable: zv", store.isLearned("1-0001", "zv"), true);
eq("old entry has no wr", store.isLearned("1-0001", "wr"), false);
eq("stats of old data", store.levelStats(1), { zv: 1, vz: 1, wr: 0, any: 2 });

store.setLearned("1-0003", "wr", true);
eq("wr set", store.isLearned("1-0003", "wr"), true);
eq("wr does not touch zv/vz", [store.isLearned("1-0003", "zv"), store.isLearned("1-0003", "vz")], [false, false]);
eq("wr saved", saved()["1-0003"], { zv: 0, vz: 0, wr: 1 });
eq("stats count wr and any", store.levelStats(1), { zv: 1, vz: 1, wr: 1, any: 3 });

store.setLearned("1-0001", "wr", true);
eq("wr added to an old entry", saved()["1-0001"], { zv: 1, vz: 0, wr: 1 });
store.setLearned("1-0001", "wr", false);
eq("wr removed, old shape back", saved()["1-0001"], { zv: 1, vz: 0 });

store.setLearned("1-0003", "wr", false);
eq("entry deleted when all directions are 0", "1-0003" in saved(), false);
store.setLearned("1-0002", "vz", false);
eq("entry deleted when last direction is unset", "1-0002" in saved(), false);

store.setLearned("2-0001", "wr", true);
eq("levels are counted separately", [store.levelStats(1).wr, store.levelStats(2).wr], [0, 1]);
eq("stats limited to real ids", store.levelStats(2, [{ id: "2-0009" }]).wr, 0);

eq("import old backup (no wr)", store.importProgress(JSON.stringify({ "3-0001": { zv: 1, vz: 0 } })), 1);
eq("old backup kept as is", saved(), { "3-0001": { zv: 1, vz: 0 } });
eq("import backup with wr", store.importProgress(JSON.stringify({ "3-0001": { zv: 0, vz: 0, wr: 1 }, "3-0002": { zv: 1, vz: 1 } })), 2);
eq("wr survives import", saved()["3-0001"], { zv: 0, vz: 0, wr: 1 });
eq("export round-trips", JSON.parse(store.exportProgress()), saved());
let threw = false;
try { store.importProgress(JSON.stringify({ "nope": { zv: 1 } })); } catch (e) { threw = true; }
eq("bad id rejected", threw, true);

store.resetLevel(3);
eq("reset clears every direction of the level", saved(), {});

eq("settings defaults", [store.getSettings().writingOutline, store.getSettings().writingPinyin], [false, true]);
store.updateSettings({ writingOutline: true });
eq("setting saved", JSON.parse(mem.get("hskfc.v1.settings")).writingOutline, true);

// ---- Trắc nghiệm progress (Phase 9): per word, own key, reset per level, backup key _quiz
const quizSaved = () => JSON.parse(mem.get("hskfc.v1.quiz") || "{}");
eq("quiz empty at first", store.getQuiz(), {});
eq("quiz settings defaults", [store.getSettings().quizPool, store.getSettings().quizSize, store.getSettings().quizTypes.length], ["all", 20, 6]);
store.setQuizEntry("1-0001", { ok: 1, wrong: 0 });
store.setQuizEntry("1-0002", { ok: 0, wrong: 2 });
store.setQuizEntry("2-0001", { ok: 1, wrong: 1 });
eq("quiz saved under its own key", quizSaved(), { "1-0001": { ok: 1, wrong: 0 }, "1-0002": { ok: 0, wrong: 2 }, "2-0001": { ok: 1, wrong: 1 } });
eq("quiz progress does not touch flashcard progress", saved(), {});
store.setLearned("1-0005", "zv", true);
let out = JSON.parse(store.exportProgress());
eq("export has _quiz when not empty", out._quiz, quizSaved());
eq("export has no _bank while the bank is empty", "_bank" in out, false);
const backup = store.exportProgress();
store.resetQuizLevel(1);
eq("reset clears only that level", quizSaved(), { "2-0001": { ok: 1, wrong: 1 } });
eq("reset leaves flashcard progress alone", saved()["1-0005"], { zv: 1, vz: 0 });
eq("restore a backup with _quiz", store.importProgress(backup), 1);
eq("quiz progress restored", store.getQuiz(), { "1-0001": { ok: 1, wrong: 0 }, "1-0002": { ok: 0, wrong: 2 }, "2-0001": { ok: 1, wrong: 1 } });
eq("quiz count in backup", store.quizCountInBackup(backup), 3);
store.importProgress(JSON.stringify({ "1-0005": { zv: 1, vz: 0 } })); // old backup: no _quiz
eq("old backup without _quiz leaves the quiz progress alone", store.getQuiz(), { "1-0001": { ok: 1, wrong: 0 }, "1-0002": { ok: 0, wrong: 2 }, "2-0001": { ok: 1, wrong: 1 } });
threw = false;
try { store.importProgress(JSON.stringify({ _quiz: { nope: { ok: 1 } } })); } catch (e) { threw = true; }
eq("bad quiz id rejected", threw, true);
store.importProgress(JSON.stringify({ _quiz: { "3-0001": { ok: "yes", wrong: -4 } } }));
eq("quiz entries are cleaned", store.getQuiz(), { "3-0001": { ok: 1, wrong: 0 } });
store.resetQuizLevel(3);
eq("export leaves _quiz out when empty", "_quiz" in JSON.parse(store.exportProgress()), false);

console.log(fail ? `${fail} FAILED` : "storage: all passed");
process.exit(fail ? 1 : 0);
