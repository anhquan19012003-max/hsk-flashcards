import * as store from "./js/storage.js";
import { checkAnswer } from "./js/check.js";
import { initSpeech, speak, listVoices, setVoice } from "./js/speech.js";
import { mountWriter } from "./js/writing.js";
import * as bank from "./js/bank.js";

const LEVELS = [1, 2, 3, 4, 5];
const COUNTS = { 1: 500, 2: 772, 3: 973, 4: 1000, 5: 1300 };
const DIR_LABEL = { zv: "Trung → Việt", vz: "Việt → Trung", wr: "Luyện viết" };
const dirText = (dir) => (dir === "wr" ? "Luyện viết" : `chiều ${DIR_LABEL[dir]}`);
const SIZE_OPTIONS = [10, 20, 50, 0];
const $app = document.getElementById("app");
const $toast = document.getElementById("toast");
const $modal = document.getElementById("modal-root");

const levelCache = {};
let view = { name: "home" };
let session = null;
let activeWriter = null; // writing UI mounted in the current study card
let sheet = null; // "✍️ Viết" sheet over a card: { el, word, writer }

// ---------- helpers ----------
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function shuffle(list) {
  const a = list.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function randInt(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

let toastTimer = null;
function toast(message, ms = 3000) {
  $toast.textContent = message;
  $toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $toast.classList.remove("show"), ms);
}

/** In-app dialog (no alert/confirm/prompt). Resolves with the chosen button's value, or null if dismissed. */
function dialog({ title, message = "", buttons }) {
  return new Promise((resolve) => {
    const previousFocus = document.activeElement;
    $modal.innerHTML = `
      <div class="overlay" data-dismiss="1">
        <div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-title">
          <h2 id="dlg-title">${esc(title)}</h2>
          ${message ? `<p>${esc(message)}</p>` : ""}
          <div class="stack">
            ${buttons.map((b, i) => `<button class="btn ${b.kind || ""}" data-i="${i}" ${b.disabled ? "disabled" : ""}>${esc(b.label)}</button>`).join("")}
          </div>
        </div>
      </div>`;
    const close = (value) => {
      $modal.innerHTML = "";
      document.removeEventListener("keydown", onKey);
      if (previousFocus && previousFocus.focus) previousFocus.focus();
      resolve(value);
    };
    const onKey = (e) => { if (e.key === "Escape") close(null); };
    document.addEventListener("keydown", onKey);
    $modal.querySelector(".overlay").addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-i]");
      if (btn) close(buttons[Number(btn.dataset.i)].value);
      else if (e.target.dataset.dismiss) close(null);
    });
    const first = $modal.querySelector("button:not([disabled])");
    if (first) first.focus();
  });
}

async function loadLevel(level) {
  if (levelCache[level]) return levelCache[level];
  const res = await fetch(`data/hsk${level}.json`);
  if (!res.ok) throw new Error("HTTP " + res.status);
  levelCache[level] = (await res.json()).words;
  return levelCache[level];
}

// ---------- navigation ----------
function go(next, { replace = false } = {}) {
  view = next;
  const state = { name: next.name, level: next.level };
  try {
    if (replace) history.replaceState(state, "");
    else history.pushState(state, "");
  } catch (e) { /* history unavailable: ignore */ }
  render();
  window.scrollTo(0, 0);
}

// Hardware/browser back: study, summary and "done" screens all fall back to their level screen.
window.addEventListener("popstate", (e) => {
  if (sheet) { closeSheetDom(); return; }
  const s = e.state;
  if (!s || s.name === "home") view = { name: "home" };
  else if (s.name === "settings") view = { name: "settings" };
  else if (s.name === "bank") view = { name: "bank" };
  else if (s.name.startsWith("bank-")) view = { name: "bank-level", level: s.level }; // question/summary screens fall back to the list
  else view = { name: "level", level: s.level };
  session = null;
  bank.endSession();
  render();
});

function currentLevel() {
  return view.level ?? view.done?.level ?? session?.level ?? 1;
}

// ---------- rendering ----------
function render() {
  if (activeWriter) { activeWriter.destroy(); activeWriter = null; }
  const screens = { home: renderHome, level: renderLevel, study: renderStudy, summary: renderSummary, done: renderDone, settings: renderSettings,
    bank: bank.renderBankHome, "bank-level": bank.renderBankLevel, "bank-q": bank.renderBankQuestion, "bank-sum": bank.renderBankSummary };
  $app.innerHTML = '<div class="loading">Đang tải…</div>';
  const result = (screens[view.name] || renderHome)();
  if (result && typeof result.then === "function") {
    result.then(draw).catch((err) => {
      console.error(err);
      draw(`<div class="screen error"><p>Không tải được dữ liệu. Hãy kiểm tra kết nối mạng rồi thử lại.</p>
        <button class="btn primary" data-action="retry">Thử lại</button>
        <button class="btn" data-action="home">Về trang chủ</button></div>`);
    });
  } else {
    draw(result);
  }
}

function draw(html) {
  $app.innerHTML = html;
  const input = document.getElementById("answer");
  if (input) input.focus({ preventScroll: true });
  mountSessionWriter();
  bank.afterDraw();
}

function writerOptions(extra) {
  return {
    outline: store.getSettings().writingOutline,
    onOutlineChange: (on) => store.updateSettings({ writingOutline: on }),
    ...extra,
  };
}

/** The Luyện viết card front has an empty #writer-root; fill it with the writing UI for the current word. */
function mountSessionWriter() {
  const root = document.getElementById("writer-root");
  if (!root || !session || view.name !== "study") return;
  const word = session.queue[0];
  activeWriter = mountWriter(root, word, writerOptions({
    onFinish: (summary) => {
      if (!session || session.queue[0] !== word || session.flipped) return;
      session.result = { write: summary };
      session.flipped = true;
      render();
      window.scrollTo(0, 0);
    },
  }));
}

function topBar({ title, back, gear }) {
  return `<div class="top">
    ${back ? `<button class="icon-btn" data-action="${back}" aria-label="Quay lại">←</button>` : ""}
    ${gear ? `<h1>${esc(title)}</h1><button class="icon-btn" data-action="settings" aria-label="Cài đặt">⚙️</button>` : `<div class="title">${esc(title)}</div><span style="width:48px"></span>`}
  </div>`;
}

function renderHome() {
  const buttons = LEVELS.map((n) => {
    const stats = store.levelStats(n);
    const pct = Math.round((stats.any / COUNTS[n]) * 100);
    return `<button class="level-btn" data-action="level" data-level="${n}">
      <span class="lv">HSK ${n}</span>
      <span class="sub">${COUNTS[n]} từ · Đã thuộc ${stats.any}</span>
      <div class="bar"><i style="width:${pct}%"></i></div>
    </button>`;
  }).join("");
  return `<div class="screen">${topBar({ title: "Thẻ từ vựng HSK", gear: true })}<div class="stack">${buttons}
    <button class="bank-btn" data-action="bank-open"><span class="lv">📝 Luyện đề</span>
      <span class="sub">Câu hỏi từ đề thi mẫu · Nghe · Đọc · Sắp xếp câu</span></button></div></div>`;
}

async function renderLevel() {
  const n = view.level;
  const words = await loadLevel(n);
  const stats = store.levelStats(n, words);
  const remain = { zv: words.length - stats.zv, vz: words.length - stats.vz, wr: words.length - stats.wr };
  return `<div class="screen">
    ${topBar({ title: `HSK ${n}`, back: "home" })}
    <div class="stack">
      <button class="btn primary" data-action="study" data-dir="zv">Trung → Việt<small>Còn ${remain.zv} từ</small></button>
      <button class="btn primary" data-action="study" data-dir="vz">Việt → Trung (gõ đáp án)<small>Còn ${remain.vz} từ</small></button>
      <button class="btn primary" data-action="study" data-dir="wr">Luyện viết ✍️<small>Còn ${remain.wr} từ</small></button>
      <button class="btn" data-action="review-pick">Ôn lại từ đã thuộc<small>Trung → Việt: ${stats.zv} · Việt → Trung: ${stats.vz} · Luyện viết: ${stats.wr}</small></button>
      <button class="btn danger" data-action="reset-level">Học lại từ đầu</button>
      <button class="btn" data-action="home">← Chọn cấp độ khác</button>
    </div>
  </div>`;
}

function renderDone() {
  const { level, dir, mode } = view.done;
  const reviewing = mode === "review";
  const text = reviewing
    ? `Chưa có từ nào đã thuộc trong HSK ${level} (${dirText(dir)}).`
    : `Bạn đã thuộc hết HSK ${level} (${dirText(dir)})!`;
  return `<div class="screen center">
    ${topBar({ title: `HSK ${level}`, back: "level-back" })}
    <div class="big-emoji">${reviewing ? "📭" : "🎉"}</div>
    <h2>${esc(text)}</h2>
    <div class="stack" style="margin-top:16px">
      ${reviewing ? "" : `<button class="btn primary" data-action="review" data-dir="${dir}">Ôn lại</button>`}
      ${reviewing ? "" : `<button class="btn danger" data-action="reset-level">Học lại từ đầu</button>`}
      <button class="btn" data-action="level-back">← Quay lại</button>
    </div>
  </div>`;
}

function highlight(zh, hanzi) {
  const forms = [...new Set([hanzi.replace(/[()（）]/g, ""), hanzi.replace(/[(（][^)）]*[)）]/g, "")])]
    .filter(Boolean).sort((a, b) => b.length - a.length);
  for (const f of forms) {
    const i = zh.indexOf(f);
    if (i >= 0) return `${esc(zh.slice(0, i))}<mark>${esc(f)}</mark>${esc(zh.slice(i + f.length))}`;
  }
  const chars = [...hanzi.replace(/[()（）]/g, "")];
  if (chars.length === 2) { // separable verb such as 洗了个澡
    const a = zh.indexOf(chars[0]);
    const b = a >= 0 ? zh.indexOf(chars[1], a + 1) : -1;
    if (b > a) {
      return `${esc(zh.slice(0, a))}<mark>${esc(chars[0])}</mark>${esc(zh.slice(a + 1, b))}<mark>${esc(chars[1])}</mark>${esc(zh.slice(b + 1))}`;
    }
  }
  return esc(zh);
}

function cardFront(word, s) {
  if (s.dir === "wr") {
    return `<div class="card wr-prompt">
        <div class="meaning-big">${esc(word.meaning)}</div>
        ${word.pos ? `<div class="pos">${esc(word.pos)}</div>` : ""}
        <div class="wr-line">${store.getSettings().writingPinyin ? `<span class="pinyin">${esc(word.pinyin)}</span>` : ""}
          <button class="speak" data-action="speak-word" aria-label="Nghe phát âm">🔊</button></div>
      </div>
      <div id="writer-root" class="wr-root"></div>`;
  }
  if (s.dir === "zv") {
    const long = [...word.hanzi].length > 3 ? " long" : "";
    return `<div class="card front-zh" data-action="flip" role="button" tabindex="0" aria-label="Lật thẻ">
        <div class="hanzi-big${long}">${esc(word.hanzi)}</div>
        <div style="margin-top:12px"><button class="speak" data-action="speak-word" aria-label="Nghe phát âm">🔊</button></div>
        <p class="hint">Chạm vào thẻ để lật</p>
      </div>
      <div class="spacer"></div>
      <div class="actions"><button class="btn primary" data-action="flip">Lật thẻ</button></div>`;
  }
  return `<div class="card">
      <div class="meaning-big">${esc(word.meaning)}</div>
      ${word.pos ? `<div class="pos">${esc(word.pos)}</div>` : ""}
    </div>
    <form class="answer-form" id="answer-form" autocomplete="off">
      <input id="answer" type="text" autocapitalize="off" autocorrect="off" spellcheck="false" autocomplete="off"
        enterkeyhint="done" placeholder="Gõ chữ Hán hoặc pinyin" aria-label="Đáp án">
      <button class="btn primary" type="submit">Kiểm tra</button>
    </form>
    <button class="btn" data-action="flip">Lật thẻ</button>`;
}

function typedResult(r) {
  return `<div class="result ${r.ok ? "ok" : "no"}">${r.ok ? "✅ Đúng" : "❌ Chưa đúng"}
    ${r.typed ? `<div class="typed">Bạn gõ: ${esc(r.typed)}</div>` : ""}</div>`;
}

function writeResult(w) {
  const ok = w.mistakes === 0 && w.skipped === 0;
  return `<div class="result ${ok ? "ok" : "no"}">${ok ? "✅ Viết đúng" : `Sai ${w.mistakes} nét · Bỏ qua ${w.skipped} chữ`}</div>`;
}

function cardBack(word, s) {
  const ex = word.example;
  const result = s.result ? (s.result.write ? writeResult(s.result.write) : typedResult(s.result)) : "";
  const yes = s.mode === "review" ? "Vẫn nhớ ✓" : "Đã thuộc ✓";
  const no = s.mode === "review" ? "Quên rồi ✗" : "Chưa thuộc ✗";
  return `${result}
    <div class="card">
      <div class="hz-row"><span class="hanzi-mid">${esc(word.hanzi)}</span>
        <button class="speak" data-action="speak-word" aria-label="Nghe phát âm">🔊</button>
        <button class="pill" data-action="write-open" title="Luyện viết từ này">✍️ Viết</button></div>
      <div class="pinyin">${esc(word.pinyin)}</div>
      ${word.hanviet ? `<div class="info"><span class="label">Hán Việt:</span> ${esc(word.hanviet)}</div>` : ""}
      ${word.pos ? `<div class="info"><span class="label">Từ loại:</span> ${esc(word.pos)}</div>` : ""}
      <div class="meaning">${esc(word.meaning)}</div>
      ${ex && ex.zh ? `<div class="example">
          <div class="row"><div class="zh">${highlight(ex.zh, word.hanzi)}</div>
            <button class="speak" data-action="speak-sentence" aria-label="Nghe câu ví dụ">🔊</button></div>
          ${ex.pinyin ? `<div class="py">${esc(ex.pinyin)}</div>` : ""}
          ${ex.vi ? `<div class="vi">${esc(ex.vi)}</div>` : ""}
        </div>` : ""}
    </div>
    <div class="spacer"></div>
    <div class="actions">
      <button class="btn bad" data-action="mark-no">${no}</button>
      <button class="btn good" data-action="mark-yes">${yes}</button>
    </div>`;
}

function renderStudy() {
  if (!session) return renderLevelFallback();
  const s = session;
  const word = s.queue[0];
  const pos = Math.min(s.done + 1, s.total);
  return `<div class="screen">
    ${topBar({ title: `${pos} / ${s.total}`, back: "exit-session" })}
    <div class="progress"><i style="width:${Math.round((s.done / s.total) * 100)}%"></i></div>
    ${s.flipped ? cardBack(word, s) : cardFront(word, s)}
  </div>`;
}

function renderLevelFallback() {
  view = { name: "level", level: view.level || 1 };
  return renderLevel();
}

function renderSummary() {
  const s = session;
  const review = s.mode === "review";
  return `<div class="screen center">
    ${topBar({ title: `HSK ${s.level} · ${DIR_LABEL[s.dir]}`, back: "level-back" })}
    <div class="big-emoji">🎉</div>
    <h2>Hoàn thành!</h2>
    <div class="stats">
      <div class="stat good"><b>${review ? s.kept : s.learned}</b>${review ? "Vẫn nhớ" : "Đã thuộc"}</div>
      <div class="stat bad"><b>${review ? s.forgot : s.retried.size}</b>${review ? "Quên rồi" : "Chưa thuộc"}</div>
    </div>
    <div class="stack">
      <button class="btn primary" data-action="${review ? "review" : "study"}" data-dir="${s.dir}">${review ? "Ôn tiếp" : "Học tiếp"}</button>
      <button class="btn" data-action="home">Về trang chủ</button>
    </div>
  </div>`;
}

function voiceSelect(current) {
  const voices = listVoices();
  if (voices.length === 0) return `<p class="note">Máy chưa có giọng đọc tiếng Trung. iPhone: Cài đặt → Trợ năng → Nội dung được đọc → Giọng nói → Tiếng Trung. Android: Cài đặt → Chuyển văn bản thành giọng nói.</p>`;
  const options = [`<option value=""${current ? "" : " selected"}>Tự động</option>`]
    .concat(voices.map((v) => `<option value="${esc(v.uri)}"${v.uri === current ? " selected" : ""}>${esc(v.name)} (${esc(v.lang)})</option>`));
  return `<select class="select" id="voice-select" aria-label="Giọng đọc">${options.join("")}</select>
    <p class="note">Muốn giọng tự nhiên hơn? Tải giọng “Nâng cao” trong cài đặt của máy, rồi mở lại ứng dụng.</p>`;
}

async function renderSettings() {
  const st = store.getSettings();
  const bankSection = await bank.settingsSection();
  const seg = (items, current, action) => `<div class="seg">${items.map(([value, label]) =>
    `<button data-action="${action}" data-value="${value}" aria-pressed="${String(current) === String(value)}">${label}</button>`).join("")}</div>`;
  return `<div class="screen">
    ${topBar({ title: "Cài đặt", back: "back" })}
    <div class="stack">
      <div class="section"><h2>Số thẻ mỗi lượt học</h2>
        ${seg(SIZE_OPTIONS.map((n) => [n, n === 0 ? "Tất cả" : n]), st.sessionSize, "set-size")}</div>
      <div class="section"><h2>Tốc độ đọc</h2>
        ${seg([["slow", "Chậm"], ["normal", "Bình thường"]], st.speed, "set-speed")}</div>
      <div class="section"><h2>Giọng đọc</h2>
        ${voiceSelect(st.voice)}
        <button class="btn" style="margin-top:10px" data-action="test-voice">🔊 Thử giọng đọc</button></div>
      <div class="section"><h2>Luyện viết</h2>
        <p class="setting-label">Hiện chữ mờ khi bắt đầu</p>
        ${seg([[1, "Bật"], [0, "Tắt"]], st.writingOutline ? 1 : 0, "set-outline")}
        <p class="setting-label">Hiện pinyin khi luyện viết</p>
        ${seg([[1, "Bật"], [0, "Tắt"]], st.writingPinyin ? 1 : 0, "set-wpinyin")}</div>
      ${bankSection}
      <div class="section"><h2>Tiến độ học</h2>
        <div class="stack">
          <button class="btn" data-action="backup">Sao lưu tiến độ</button>
          <button class="btn" data-action="restore">Khôi phục tiến độ</button>
          <input type="file" id="restore-file" accept="application/json,.json" hidden>
        </div>
        <p class="note">Tiến độ chỉ lưu trên máy này. Hãy sao lưu trước khi đổi điện thoại hoặc xóa dữ liệu trình duyệt.</p></div>
      <div class="section"><details><summary>Cách cài lên điện thoại</summary>
        <ul>
          <li><b>iPhone:</b> mở bằng Safari → nút Chia sẻ → Thêm vào MH chính.</li>
          <li><b>Android:</b> mở bằng Chrome → menu ⋮ → Cài đặt ứng dụng (hoặc Thêm vào màn hình chính).</li>
        </ul></details></div>
      <p class="note">Nguồn & giấy phép: Luyện viết dùng Hanzi Writer (MIT) và dữ liệu nét chữ từ Make Me a Hanzi / Arphic (Arphic Public License).</p>
    </div>
  </div>`;
}

// ---------- study logic ----------
async function startSession(level, dir, mode) {
  const words = await loadLevel(level);
  const pool = words.filter((w) => store.isLearned(w.id, dir) === (mode === "review"));
  // starting again from a summary/"done" screen replaces it, so Back always returns to the level screen
  const replace = view.name === "summary" || view.name === "done";
  if (pool.length === 0) {
    session = null;
    go({ name: "done", level, done: { level, dir, mode } }, { replace });
    return;
  }
  const size = store.getSettings().sessionSize;
  const queue = shuffle(pool).slice(0, size > 0 ? size : pool.length);
  session = { level, dir, mode, queue, total: queue.length, done: 0, learned: 0, kept: 0, forgot: 0,
    retried: new Set(), flipped: false, result: null };
  go({ name: "study", level }, { replace });
}

function answerCurrent(yes) {
  const s = session;
  const word = s.queue.shift();
  if (s.mode === "review") {
    if (yes) s.kept++;
    else { s.forgot++; store.setLearned(word.id, s.dir, false); }
    s.done++;
  } else if (yes) {
    store.setLearned(word.id, s.dir, true);
    s.learned++;
    s.done++;
  } else {
    s.retried.add(word.id);
    s.queue.splice(Math.min(s.queue.length, randInt(4, 7)), 0, word); // comes back as the 5th–8th card from now
  }
  s.flipped = false;
  s.result = null;
  if (s.queue.length === 0) go({ name: "summary", level: s.level }, { replace: true });
  else { render(); window.scrollTo(0, 0); }
}

function flip() {
  if (!session || session.flipped) return;
  session.flipped = true;
  render();
  window.scrollTo(0, 0);
}

function onSpeakProblem() {
  toast("Máy chưa có giọng đọc tiếng Trung. Android: Cài đặt → Chuyển văn bản thành giọng nói → tải tiếng Trung.", 7000);
}

function say(text, kind) {
  speak(text, kind, store.getSettings().speed, onSpeakProblem);
}

// ---------- events ----------
document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const { action, level, dir, value } = el.dataset;
  switch (action) {
    case "home": session = null; go({ name: "home" }); break;
    case "retry": render(); break;
    case "settings": go({ name: "settings" }); break;
    case "back": history.length > 1 ? history.back() : go({ name: "home" }); break;
    case "level": go({ name: "level", level: Number(level) }); break;
    case "level-back": case "exit-session": history.back(); break;
    case "study": await startSession(currentLevel(), dir, "study"); break;
    case "review": await startSession(currentLevel(), dir, "review"); break;
    case "review-pick": {
      const words = await loadLevel(view.level);
      const stats = store.levelStats(view.level, words);
      const choice = await dialog({
        title: "Ôn lại chiều nào?",
        buttons: [
          { label: `Trung → Việt (${stats.zv} từ)`, value: "zv", kind: "primary", disabled: stats.zv === 0 },
          { label: `Việt → Trung (${stats.vz} từ)`, value: "vz", kind: "primary", disabled: stats.vz === 0 },
          { label: `Luyện viết (${stats.wr} từ)`, value: "wr", kind: "primary", disabled: stats.wr === 0 },
          { label: "Hủy", value: null },
        ],
      });
      if (choice) await startSession(view.level, choice, "review");
      break;
    }
    case "reset-level": {
      const n = currentLevel();
      const yes = await dialog({
        title: `Học lại HSK ${n} từ đầu?`,
        message: "Toàn bộ tiến độ của cấp độ này (mọi chiều) sẽ bị xóa.",
        buttons: [{ label: "Xóa và học lại", value: true, kind: "good" }, { label: "Hủy", value: null }],
      });
      if (yes) {
        store.resetLevel(n);
        session = null;
        toast(`Đã xóa tiến độ HSK ${n}`);
        go({ name: "level", level: n }, { replace: true });
      }
      break;
    }
    case "flip": flip(); break;
    case "speak-word": e.stopPropagation(); say(session.queue[0].hanzi, "word"); break;
    case "write-open": e.stopPropagation(); openSheet(session.queue[0]); break;
    case "sheet-close": closeSheet(); break;
    case "sheet-redo": mountSheetWriter(); break;
    case "sheet-speak": say(sheet.word.hanzi, "word"); break;
    case "speak-sentence": say(session.queue[0].example.zh, "sentence"); break;
    case "mark-yes": answerCurrent(true); break;
    case "mark-no": answerCurrent(false); break;
    case "set-size": store.updateSettings({ sessionSize: Number(value) }); render(); break;
    case "set-speed": store.updateSettings({ speed: value }); render(); break;
    case "set-outline": store.updateSettings({ writingOutline: value === "1" }); render(); break;
    case "set-wpinyin": store.updateSettings({ writingPinyin: value === "1" }); render(); break;
    case "test-voice": say("你好，欢迎学习汉语。", "sentence"); break;
    case "backup": backup(); break;
    case "restore": document.getElementById("restore-file").click(); break;
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && sheet && !$modal.firstChild) { closeSheet(); return; }
  const card = e.target.closest && e.target.closest(".card[data-action='flip']");
  if (card && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); flip(); }
});

document.addEventListener("submit", (e) => {
  if (e.target.id !== "answer-form") return;
  e.preventDefault();
  const typed = document.getElementById("answer").value.trim();
  if (!typed) { toast("Hãy gõ đáp án, hoặc bấm “Lật thẻ”."); return; }
  const word = session.queue[0];
  session.result = { ok: checkAnswer(typed, word.accept), typed };
  session.flipped = true;
  render();
  window.scrollTo(0, 0);
});

document.addEventListener("change", async (e) => {
  if (e.target.id === "voice-select") {
    store.updateSettings({ voice: e.target.value });
    setVoice(e.target.value);
    say("你好，欢迎学习汉语。", "sentence");
    return;
  }
  if (e.target.id !== "restore-file") return;
  const file = e.target.files[0];
  e.target.value = "";
  if (!file) return;
  try {
    const text = await file.text();
    JSON.parse(text);
    const yes = await dialog({
      title: "Khôi phục tiến độ?",
      message: "Tiến độ hiện tại trên máy sẽ được thay bằng nội dung trong file sao lưu.",
      buttons: [{ label: "Khôi phục", value: true, kind: "primary" }, { label: "Hủy", value: null }],
    });
    if (!yes) return;
    const n = store.importProgress(text);
    const q = store.bankCountInBackup(text);
    toast(`Đã khôi phục ${n} từ` + (q ? ` và ${q} câu Luyện đề` : ""));
  } catch (err) {
    await dialog({ title: "File không hợp lệ", message: "Hãy chọn file sao lưu do ứng dụng này tạo ra.", buttons: [{ label: "Đóng", value: null, kind: "primary" }] });
  }
});

function backup() {
  const blob = new Blob([store.exportProgress()], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const d = new Date();
  a.href = url;
  a.download = `hsk-tien-do-${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast("Đã tạo file sao lưu");
}

// ---------- "✍️ Viết" sheet (practice from a card back; never changes progress) ----------
function openSheet(word) {
  if (sheet) return;
  const el = document.createElement("div");
  el.className = "sheet";
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-modal", "true");
  el.setAttribute("aria-label", "Luyện viết");
  const pinyin = store.getSettings().writingPinyin;
  el.innerHTML = `<div class="sheet-inner">
    <div class="top"><div class="title">Luyện viết</div>
      <button class="btn sheet-close" data-action="sheet-close">Đóng</button></div>
    <div class="card wr-prompt">
      <div class="meaning-big">${esc(word.meaning)}</div>
      <div class="wr-line">${pinyin ? `<span class="pinyin">${esc(word.pinyin)}</span>` : ""}
        <button class="speak" data-action="sheet-speak" aria-label="Nghe phát âm">🔊</button></div>
    </div>
    <div class="wr-root" id="sheet-writer"></div>
    <div id="sheet-result"></div>
  </div>`;
  document.body.appendChild(el);
  sheet = { el, word, writer: null };
  try { history.pushState({ name: "sheet" }, ""); } catch (e) { /* history unavailable */ }
  mountSheetWriter();
}

function mountSheetWriter() {
  if (!sheet) return;
  if (sheet.writer) sheet.writer.destroy();
  const result = sheet.el.querySelector("#sheet-result");
  result.innerHTML = "";
  sheet.writer = mountWriter(sheet.el.querySelector("#sheet-writer"), sheet.word, writerOptions({
    onFinish: (w) => {
      result.innerHTML = `${writeResult(w)}<button class="btn" data-action="sheet-redo">Viết lại cả từ</button>`;
    },
  }));
}

function closeSheetDom() {
  if (!sheet) return;
  sheet.writer?.destroy();
  sheet.el.remove();
  sheet = null;
}

function closeSheet() {
  if (!sheet) return;
  if (history.state && history.state.name === "sheet") history.back(); // popstate closes it
  else closeSheetDom();
}

// ---------- start ----------
initSpeech(store.getSettings().voice, () => { if (view.name === "settings") render(); });
bank.init({
  esc, shuffle, toast, dialog, render, go, topBar,
  getView: () => view,
  setView: (v) => { view = v; },
});
const magicKey = bank.takeMagicKey(); // removes `#k=…` from the address bar immediately
history.replaceState({ name: "home" }, "");
render();
if (magicKey) {
  bank.unlockWithRaw(magicKey).then((result) => {
    if (result === "ok") toast("Đã mở khóa Luyện đề");
    else if (result === "bad") toast("Liên kết không đúng hoặc đã cũ. Hãy nhập mật khẩu.", 6000);
    go({ name: "bank" });
  });
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => { /* offline support is optional */ });
  });
}
