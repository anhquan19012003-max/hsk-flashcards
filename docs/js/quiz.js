// Trắc nghiệm (Phase 9, specs/vocab-quiz.md): the multiple-choice vocab quiz screens. The questions come from quizcore.js,
// progress lives in storage.js (`hskfc.v1.quiz`, per word) and is separate from the flash-card progress.
import * as store from "./storage.js";
import * as core from "./quizcore.js";
import { esc, wordCardHtml } from "./wordcard.js";

let ctx = null; // helpers injected by app.js: shuffle, toast, dialog, render, go, topBar, getView, setView, loadLevel, say, hasVoice
let gen = null; // quizcore generator
let genLevel = 0; // highest level the generator was built with (a level's wrong options may borrow from the lower ones)
let qs = null; // current set

const SIZE_OPTIONS = [10, 20, 50, 0];
const MODE_TEXT = { new: "Làm câu mới", wrong: "Làm lại câu sai" };
const LATIN = new Set(["nghia", "pinyin", "hanviet"]); // option texts that are not Chinese characters

export function init(helpers) { ctx = helpers; }
export function endSession() { qs = null; }

async function getGen(level) {
  if (!gen || genLevel < level) {
    const byLevel = {};
    for (let l = 1; l <= level; l++) byLevel[l] = await ctx.loadLevel(l);
    gen = core.createQuiz(byLevel);
    genLevel = level;
  }
  return gen;
}

const anyLearned = (id) => store.isLearned(id, "zv") || store.isLearned(id, "vz") || store.isLearned(id, "wr");
const flashLearned = (id) => store.isLearned(id, "zv") || store.isLearned(id, "vz");

function chosenTypes() {
  const raw = store.getSettings().quizTypes;
  const ok = Array.isArray(raw) ? raw.filter((t) => core.TYPE_IDS.includes(t)) : [];
  return ok.length ? ok : core.TYPE_IDS.slice();
}

/** Everything the setup screen and a new set need for one level. */
async function levelState(level) {
  const words = await ctx.loadLevel(level);
  const g = await getGen(level);
  const voice = ctx.hasVoice();
  const s = store.getSettings();
  const types = chosenTypes();
  const effective = voice ? types : types.filter((t) => t !== "nghe"); // no Chinese voice: no listening questions
  const pool = s.quizPool === "learned" ? "learned" : "all";
  const quiz = store.getQuiz();
  const eligible = core.eligibleWords(words, { gen: g, pool, types: effective, learnedFn: anyLearned, voice });
  return {
    words, gen: g, voice, types, effective, pool, quiz, eligible, size: s.quizSize,
    stats: core.quizStats(words, quiz),
    learnedCount: words.filter((w) => anyLearned(w.id)).length,
    newPool: core.candidateWords(eligible, "new", quiz),
    wrongPool: core.candidateWords(eligible, "wrong", quiz),
  };
}

// ---------- setup screen ----------
export async function renderQuizSetup() {
  qs = null;
  const level = ctx.getView().level;
  const st = await levelState(level);
  const seg = (items, current, action) => `<div class="seg">${items.map(([value, label]) =>
    `<button data-action="${action}" data-value="${value}" aria-pressed="${String(current) === String(value)}">${label}</button>`).join("")}</div>`;
  const chips = core.TYPES.filter((t) => st.voice || t.id !== "nghe").map((t) =>
    `<button class="chip" data-action="quiz-chip" data-type="${t.id}" aria-pressed="${st.types.includes(t.id)}">${t.label}</button>`).join("");
  const noVoice = st.voice ? "" : `<p class="note">Máy chưa có giọng đọc tiếng Trung nên chưa có loại “Nghe và chọn từ”. iPhone: Cài đặt → Trợ năng → Nội dung được đọc → Giọng nói → Tiếng Trung. Android: Cài đặt → Chuyển văn bản thành giọng nói.</p>`;
  const noneLearned = st.pool === "learned" && st.learnedCount === 0;
  const poolNote = noneLearned
    ? `<p class="note" id="quiz-none-learned">Bạn chưa thuộc từ nào trong HSK ${level}. Hãy học thẻ trước, hoặc chọn “Tất cả từ”.</p>` : "";
  const allDone = st.stats.total > 0 && st.stats.remaining === 0;
  const hint = (n, none) => (n ? `${n} từ` : none);
  return `<div class="screen">
    ${ctx.topBar({ title: `HSK ${level} · Trắc nghiệm`, back: "back" })}
    <div class="bank-stats">
      <div class="stat">Còn ${st.stats.remaining} từ chưa làm đúng</div>
      <div class="stat bad">Từ sai: ${st.stats.wrong}</div>
    </div>
    ${allDone ? `<div class="center" id="quiz-all-done"><div class="big-emoji">🎉</div><h2>Bạn đã làm đúng hết từ của HSK ${level}!</h2></div>` : ""}
    <div class="section"><h2>Loại câu</h2><div class="chips">${chips}</div>${noVoice}
      <h2 style="margin-top:14px">Các từ</h2>
      ${seg([["all", "Tất cả từ"], ["learned", "Chỉ từ đã thuộc"]], st.pool, "quiz-pool")}${poolNote}
      <h2 style="margin-top:14px">Số câu mỗi lượt</h2>
      ${seg(SIZE_OPTIONS.map((n) => [n, n === 0 ? "Tất cả" : n]), st.size, "quiz-size")}</div>
    <div class="stack">
      ${allDone ? "" : `<button class="btn primary" data-action="quiz-start" data-mode="new" ${st.newPool.length ? "" : "disabled"}>Làm câu mới<small>${hint(st.newPool.length, "Không còn câu nào")}</small></button>`}
      <button class="btn ${allDone ? "primary" : ""}" data-action="quiz-start" data-mode="wrong" ${st.wrongPool.length ? "" : "disabled"}>Làm lại câu sai<small>${hint(st.wrongPool.length, "Chưa có câu sai")}</small></button>
      <button class="btn danger" data-action="quiz-reset">Làm lại từ đầu</button>
      <button class="btn" data-action="back">← Quay lại</button>
    </div>
  </div>`;
}

// ---------- sets ----------
async function startSet(mode) {
  const level = ctx.getView().level;
  const st = await levelState(level);
  const pool = mode === "wrong" ? st.wrongPool : st.newPool;
  if (!pool.length) { ctx.toast("Không còn câu nào để làm."); ctx.render(); return; }
  const picked = ctx.shuffle(pool).slice(0, st.size > 0 ? st.size : pool.length);
  qs = {
    level, mode, words: picked, types: st.effective, voice: st.voice, gen: st.gen,
    i: 0, q: null, ans: null, hint: false, correct: 0, wrong: 0, wrongWords: [], total: picked.length,
  };
  prepareQuestion();
  const v = ctx.getView();
  ctx.go({ name: qs.words.length ? "quiz-q" : "quiz-sum", level }, { replace: v.name === "quiz-sum" });
}

/** Build the question for the current word (a word that cannot get a chosen type is skipped). */
function prepareQuestion() {
  while (qs.i < qs.words.length) {
    const word = qs.words[qs.i];
    const type = core.pickType(word, qs.types, qs.gen, Math.random, qs.voice);
    const q = type ? qs.gen.make(word, type, Math.random, { voice: qs.voice }) : null;
    if (q) { qs.q = q; qs.ans = null; qs.hint = false; return; }
    qs.words.splice(qs.i, 1);
    qs.total--;
  }
  qs.q = null;
}

const currentWord = () => qs.words[qs.i];

function answer(key) {
  if (!qs || !qs.q || qs.ans) return;
  const w = currentWord();
  const ok = key === qs.q.answer;
  qs.ans = { key, ok };
  store.setQuizEntry(w.id, core.applyResult(store.getQuiz()[w.id], ok));
  if (ok) qs.correct++;
  else { qs.wrong++; qs.wrongWords.push(w); }
  ctx.render();
  setTimeout(() => document.querySelector(".quiz-fb")?.scrollIntoView({ block: "nearest", behavior: "smooth" }), 50);
}

function next() {
  if (!qs || !qs.ans) return;
  qs.i++;
  prepareQuestion();
  if (!qs.q) { ctx.go({ name: "quiz-sum", level: qs.level }, { replace: true }); return; }
  ctx.render();
  window.scrollTo(0, 0);
  if (qs.q.type === "nghe") ctx.say(currentWord().hanzi, "word"); // the tap on `Tiếp` lets the next listening question play by itself
}

// ---------- question screen ----------
function promptHtml(w, q) {
  const long = [...w.hanzi].length > 3 ? " long" : "";
  switch (q.type) {
    case "nghia":
      return `<div class="qprompt"><div class="hanzi-big${long}">${esc(w.hanzi)}</div>
        <button class="speak" data-action="quiz-speak-prompt" aria-label="Nghe phát âm">🔊</button></div>`;
    case "pinyin": case "hanviet":
      return `<div class="qprompt"><div class="hanzi-big${long}">${esc(w.hanzi)}</div></div>`;
    case "chuhan":
      return `<div class="qprompt"><div class="meaning-big">${esc(w.meaning)}</div>${w.pos ? `<div class="pos">${esc(w.pos)}</div>` : ""}</div>`;
    case "nghe":
      return `<div class="audio-bar quiz-listen">
        <button class="btn primary" data-action="quiz-speak-prompt">🔊 Nghe</button>
        <button class="btn" data-action="quiz-speak-prompt">🔁 Nghe lại</button></div>`;
    case "dientu": {
      const blank = core.blankSentence(w) || "";
      const shown = qs.hint || qs.ans;
      return `<div class="qprompt"><div class="quiz-sentence zh">${esc(blank)}</div>
        ${shown ? `<div class="vi-hint" id="quiz-hint-text">${esc(w.example.vi || "")}</div>`
          : `<button class="btn small" data-action="quiz-hint">Gợi ý</button>`}</div>`;
    }
    default: return "";
  }
}

function optionHtml(o, q, a) {
  let cls = "opt";
  if (a) {
    if (o.key === q.answer) cls += " correct";
    else if (o.key === a.key) cls += " wrong";
  }
  return `<button class="${cls}" data-action="quiz-pick" data-key="${o.key}" ${a ? "disabled" : ""}>
    <span class="k">${o.key}</span><span class="t${LATIN.has(q.type) ? " vi" : ""}">${esc(o.text)}</span></button>`;
}

export function renderQuizQuestion() {
  if (!qs || !qs.q) {
    ctx.setView({ name: "quiz", level: ctx.getView().level });
    return renderQuizSetup();
  }
  const w = currentWord(), q = qs.q, a = qs.ans;
  const label = core.TYPES.find((t) => t.id === q.type).label;
  const last = qs.i === qs.words.length - 1;
  const addBtn = a && !a.ok && flashLearned(w.id)
    ? `<button class="btn small" data-action="quiz-review">Thêm vào ôn tập</button>` : "";
  // the right key is also in the DOM (data-answer) so tests can answer; the whole app runs on the phone anyway
  return `<div class="screen">
    ${ctx.topBar({ title: `HSK ${qs.level} · Trắc nghiệm`, back: "exit-session" })}
    <div class="progress"><i style="width:${Math.round((qs.i / qs.total) * 100)}%"></i></div>
    <div class="qhead"><b>Câu ${qs.i + 1} / ${qs.total}</b><span class="qtype">${label}</span></div>
    <div class="qcard" data-wid="${esc(w.id)}" data-type="${q.type}" data-answer="${q.answer}">
      ${promptHtml(w, q)}
      <div class="opt-grid">${q.options.map((o) => optionHtml(o, q, a)).join("")}</div>
      ${a ? `<div class="fb quiz-fb ${a.ok ? "ok" : "no"}"><b>${a.ok ? "✅ Đúng" : "❌ Chưa đúng"}</b>${addBtn}</div>` : ""}
    </div>
    ${a ? wordCardHtml(w, { speakWord: "quiz-speak-word", speakSentence: "quiz-speak-sent", extraClass: "quiz-card" }) : ""}
    <div class="spacer"></div>
    <div class="actions"><button class="btn primary" data-action="quiz-next" ${a ? "" : "disabled"}>${last ? "Xong" : "Tiếp"}</button></div>
  </div>`;
}

// ---------- end of set ----------
export function renderQuizSummary() {
  if (!qs) {
    ctx.setView({ name: "quiz", level: ctx.getView().level });
    return renderQuizSetup();
  }
  const s = qs;
  const wrongList = s.wrongWords.length
    ? `<div class="section wrong-list"><h2>Từ làm sai</h2>${s.wrongWords.map((w) =>
      `<div class="wrow"><span class="zh">${esc(w.hanzi)}</span> · <span class="py">${esc(w.pinyin)}</span> · ${esc(w.meaning)}</div>`).join("")}</div>`
    : "";
  return `<div class="screen center">
    ${ctx.topBar({ title: `HSK ${s.level} · Trắc nghiệm`, back: "level-back" })}
    <div class="big-emoji">🎉</div><h2>Hoàn thành!</h2>
    <p class="note">${MODE_TEXT[s.mode]}</p>
    <div class="stats">
      <div class="stat good"><b>${s.correct}</b>Đúng</div>
      <div class="stat bad"><b>${s.wrong}</b>Sai</div>
    </div>
    <p><b>${s.correct} / ${s.total}</b> câu đúng</p>
    ${wrongList}
    <div class="stack">
      <button class="btn primary" data-action="quiz-again">Làm tiếp</button>
      <button class="btn" data-action="quiz-tolevel">Về cấp độ</button>
    </div>
  </div>`;
}

// ---------- events ----------
document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-action^='quiz-']");
  if (!el || !ctx) return;
  const d = el.dataset;
  switch (d.action) {
    case "quiz-open": ctx.go({ name: "quiz", level: ctx.getView().level }); break;
    case "quiz-chip": {
      const now = chosenTypes();
      const nextTypes = now.includes(d.type) ? now.filter((t) => t !== d.type) : [...now, d.type];
      if (!nextTypes.length) { ctx.toast("Cần chọn ít nhất một loại câu."); break; }
      store.updateSettings({ quizTypes: core.TYPE_IDS.filter((t) => nextTypes.includes(t)) });
      ctx.render();
      break;
    }
    case "quiz-pool": store.updateSettings({ quizPool: d.value === "learned" ? "learned" : "all" }); ctx.render(); break;
    case "quiz-size": store.updateSettings({ quizSize: Number(d.value) }); ctx.render(); break;
    case "quiz-start": await startSet(d.mode); break;
    case "quiz-again": await startSet(qs ? qs.mode : "new"); break;
    case "quiz-tolevel": ctx.go({ name: "level", level: qs ? qs.level : ctx.getView().level }, { replace: true }); break;
    case "quiz-reset": {
      const level = ctx.getView().level;
      const yes = await ctx.dialog({
        title: `Làm lại Trắc nghiệm HSK ${level} từ đầu?`,
        message: "Kết quả Trắc nghiệm của cấp độ này sẽ bị xóa. Tiến độ học thẻ không bị ảnh hưởng.",
        buttons: [{ label: "Xóa và làm lại", value: true, kind: "good" }, { label: "Hủy", value: null }],
      });
      if (yes) { store.resetQuizLevel(level); ctx.toast(`Đã xóa kết quả Trắc nghiệm HSK ${level}`); ctx.render(); }
      break;
    }
    case "quiz-pick": answer(d.key); break;
    case "quiz-next": next(); break;
    case "quiz-hint": if (qs) { qs.hint = true; ctx.render(); } break;
    case "quiz-speak-prompt": case "quiz-speak-word": if (qs) ctx.say(currentWord().hanzi, "word"); break;
    case "quiz-speak-sent": if (qs) ctx.say(currentWord().example.zh, "sentence"); break;
    case "quiz-review": {
      const w = currentWord();
      store.setLearned(w.id, "zv", false);
      store.setLearned(w.id, "vz", false);
      ctx.toast("Đã thêm vào ôn tập");
      ctx.render();
      break;
    }
  }
});
