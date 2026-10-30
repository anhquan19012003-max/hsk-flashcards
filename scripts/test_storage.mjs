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

console.log(fail ? `${fail} FAILED` : "storage: all passed");
process.exit(fail ? 1 : 0);
