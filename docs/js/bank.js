// Luyện đề: the encrypted question bank (Phase 8, specs/mock-tests.md). Screens, unlocking, audio, progress.
import * as store from "./storage.js";
import * as core from "./bankcore.js";
import { fetchMeta, keyFromPassword, keyFromRaw, keyMatches, decryptBlob, loadStoredKey, storeKey, clearStoredKey } from "./bankcrypto.js";

let ctx = null; // helpers injected by app.js: esc, shuffle, toast, dialog, render, go, topBar
let meta; // undefined = not fetched yet, null = no bank published, "error" = could not fetch, else the meta object
let key = null; // CryptoKey while unlocked
let passwordChanged = false;
const indexes = {}; // level -> decrypted index
const mediaUrls = new Map(); // "level/name" -> object URL of a decrypted clip/image
let tab = "nghe";
const filters = { nghe: [], doc: [], sapxep: [] }; // chosen question types per tab ([] = all)
let bsession = null;
let ready = null;
const ensureReady = () => ready || (ready = load()); // meta.json is only requested once Luyện đề (or a magic link) needs it

const esc = (s) => ctx.esc(s);
const SIZE_OPTIONS = [10, 20, 0];
const MODE_TEXT = { new: "Làm câu mới", wrong: "Làm lại câu sai" };

export function init(helpers) {
  ctx = helpers;
  // At start-up only look for a saved key (no network); with one, load the bank state so Cài đặt can show its buttons.
  loadStoredKey().then((k) => { if (k) ensureReady().then(() => ctx.refresh()); });
}

async function load() {
  meta = await fetchMeta();
  const stored = await loadStoredKey();
  key = null;
  if (stored && meta && meta !== "error") {
    if (await keyMatches(stored, meta)) key = stored;
    else { await clearStoredKey(); passwordChanged = true; }
  } else if (stored && meta === "error") {
    key = stored; // offline and meta not cached: trust the saved key, decrypting the cached files will tell
  }
}

// ---------- unlocking ----------
/** Call once at start-up: returns the key from a `#k=…` magic link and removes it from the address bar at once. */
export function takeMagicKey() {
  const m = /^#k=([A-Za-z0-9_-]+)$/.exec(location.hash);
  if (!m) return null;
  try { history.replaceState(history.state, "", location.pathname + location.search); } catch (e) { /* ignore */ }
  return m[1];
}

async function setKey(k) {
  key = k;
  passwordChanged = false;
  Object.keys(indexes).forEach((l) => delete indexes[l]);
  await storeKey(k);
}

/** Returns "ok" | "bad" | "nobank". */
export async function unlockWithRaw(raw) {
  await ensureReady();
  if (!meta || meta === "error") return "nobank";
  try {
    const k = await keyFromRaw(raw);
    if (!(await keyMatches(k, meta))) return "bad";
    await setKey(k);
    return "ok";
  } catch (e) {
    return "bad";
  }
}

async function unlockWithPassword(password) {
  const k = await keyFromPassword(password, meta);
  if (!(await keyMatches(k, meta))) return false;
  await setKey(k);
  return true;
}

async function lock() {
  key = null;
  await clearStoredKey();
  Object.keys(indexes).forEach((l) => delete indexes[l]);
  stopAudio();
  mediaUrls.forEach((u) => URL.revokeObjectURL(u));
  mediaUrls.clear();
  bsession = null;
}

async function loadIndex(level) {
  if (indexes[level]) return indexes[level];
  const res = await fetch(`bank/hsk${level}/index.bin`);
  if (!res.ok) throw new Error("HTTP " + res.status);
  let plain;
  try {
    plain = await decryptBlob(key, await res.arrayBuffer());
  } catch (e) { // the key no longer fits the files: the password was changed
    await lock();
    passwordChanged = true;
    throw new Error("locked");
  }
  indexes[level] = JSON.parse(new TextDecoder().decode(plain));
  return indexes[level];
}

// ---------- media (audio clips, images) ----------
async function mediaUrl(level, name, type) {
  const id = `${level}/${name}`;
  if (mediaUrls.has(id)) return mediaUrls.get(id);
  try {
    const res = await fetch(`bank/hsk${level}/m/${name}.bin`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const plain = await decryptBlob(key, await res.arrayBuffer());
    const url = URL.createObjectURL(new Blob([plain], { type }));
    mediaUrls.set(id, url);
    return url;
  } catch (e) {
    return null;
  }
}

const player = new Audio();
globalThis.__hskBankPlayer = player; // exposed for the browser tests
let currentClip = null;
player.addEventListener("play", syncAudioButtons);
player.addEventListener("pause", syncAudioButtons);
player.addEventListener("ended", syncAudioButtons);

function syncAudioButtons() {
  document.querySelectorAll("[data-action='bank-play']").forEach((b) => {
    const on = b.dataset.clip === currentClip && !player.paused && !player.ended;
    b.textContent = on ? "⏸ Tạm dừng" : "▶ Nghe";
  });
}

function stopAudio() {
  try { player.pause(); } catch (e) { /* ignore */ }
  currentClip = null;
}

async function playClip(name, restart) {
  if (!bsession) return;
  if (!restart && currentClip === name && !player.paused && !player.ended) { player.pause(); return; }
  let url = mediaUrls.get(`${bsession.level}/${name}`);
  if (!url) {
    url = await mediaUrl(bsession.level, name, "audio/mpeg");
    if (!url) { ctx.toast("Không tải được âm thanh. Hãy kiểm tra kết nối mạng."); return; }
  }
  if (currentClip !== name) { player.src = url; currentClip = name; }
  if (restart || player.ended) player.currentTime = 0;
  try { await player.play(); } catch (e) { ctx.toast("Không phát được âm thanh."); }
}

/** After every draw: fill picture placeholders and warm up the clips of the unit on screen (iOS needs play() right inside a tap). */
export function afterDraw() {
  if (!bsession) return;
  document.querySelectorAll("img[data-bimg]").forEach(async (img) => {
    const url = await mediaUrl(bsession.level, img.dataset.bimg, "image/webp");
    if (url && img.isConnected) img.src = url;
  });
  const unit = bsession.units[bsession.unitIdx];
  if (unit && ctx.getView().name === "bank-q") for (const name of clipsOf(unit)) mediaUrl(bsession.level, name, "audio/mpeg");
}

const clipsOf = (unit) => [unit.context?.audio, ...unit.questions.map((q) => q.audio)].filter(Boolean);

// ---------- helpers ----------
function progress() { return store.getBank(); }

function paperTitle(index, unit) {
  const p = (index.papers || []).find((x) => x.id === unit.paper);
  return p ? p.title : "";
}

function unitsOf(level) { return indexes[level]?.units || []; }

// ---------- screens ----------
export async function renderBankHome() {
  stopAudio();
  bsession = null;
  await ensureReady();
  const bar = ctx.topBar({ title: "Luyện đề", back: "home" });
  if (meta === "error") {
    return `<div class="screen center">${bar}<div class="big-emoji">📡</div>
      <h2>Không tải được dữ liệu</h2><p class="note">Hãy kiểm tra kết nối mạng rồi thử lại.</p>
      <div class="stack"><button class="btn primary" data-action="bank-retry">Thử lại</button></div></div>`;
  }
  if (!meta) {
    return `<div class="screen center">${bar}<div class="big-emoji">📝</div><h2>Chưa có đề — sắp có!</h2>
      <p class="note">Ngân hàng câu hỏi đang được chuẩn bị.</p></div>`;
  }
  if (!key) {
    return `<div class="screen">${bar}
      <div class="section"><h2>Mở khóa Luyện đề</h2>
        <p class="note" id="bank-msg">${passwordChanged ? "Mật khẩu đã đổi, vui lòng nhập lại." : "Nhập mật khẩu do bạn bè gửi, hoặc mở bằng đường link riêng."}</p>
        <form class="answer-form" id="bank-unlock-form" autocomplete="off">
          <input id="bank-pw" type="password" autocapitalize="off" autocorrect="off" spellcheck="false" autocomplete="off"
            placeholder="Nhập mật khẩu" aria-label="Mật khẩu">
          <button class="btn primary" type="submit">Mở khóa</button>
        </form></div></div>`;
  }
  try {
    const rows = [];
    for (const level of meta.levels) {
      const index = await loadIndex(level);
      const st = core.levelStats(index.units, progress());
      const pct = st.total ? Math.round((st.ok / st.total) * 100) : 0;
      rows.push(`<button class="level-btn" data-action="bank-level" data-level="${level}">
        <span class="lv">HSK ${level}</span>
        <span class="sub">${st.total} câu · Đã làm đúng ${st.ok}</span>
        <div class="bar"><i style="width:${pct}%"></i></div></button>`);
    }
    return `<div class="screen">${bar}<div class="stack">${rows.join("")}</div></div>`;
  } catch (e) {
    if (!key) return renderBankHome();
    throw e;
  }
}

export async function renderBankLevel() {
  stopAudio();
  bsession = null;
  await ensureReady();
  const level = ctx.getView().level;
  if (!key) return renderBankHome();
  await loadIndex(level);
  const units = unitsOf(level);
  const st = core.tabStats(units, tab, progress());
  const size = store.getSettings().bankSize;
  const chosen = filters[tab];
  const tabs = core.TABS.map((t) => `<button data-action="bank-tab" data-tab="${t.id}" aria-pressed="${t.id === tab}">${t.label}</button>`).join("");
  const chips = core.TYPE_CHIPS[tab].map(([id, label]) =>
    `<button class="chip" data-action="bank-chip" data-type="${id}" aria-pressed="${chosen.includes(id)}">${label}</button>`).join("");
  const newPool = core.candidateUnits(units, { tab, types: chosen, mode: "new", progress: progress() });
  const wrongPool = core.candidateUnits(units, { tab, types: chosen, mode: "wrong", progress: progress() });
  return `<div class="screen">
    ${ctx.topBar({ title: `Luyện đề · HSK ${level}`, back: "back" })}
    <div class="seg bank-tabs" role="tablist">${tabs}</div>
    <div class="bank-stats">
      <div class="stat">Còn ${st.remaining} câu chưa làm đúng</div>
      <div class="stat bad">Câu sai: ${st.wrong}</div>
    </div>
    <div class="section"><h2>Loại câu</h2><div class="chips">${chips}</div>
      <h2 style="margin-top:14px">Số câu mỗi lượt</h2>
      <div class="seg">${SIZE_OPTIONS.map((n) => `<button data-action="bank-size" data-value="${n}" aria-pressed="${size === n}">${n === 0 ? "Tất cả" : n}</button>`).join("")}</div></div>
    <div class="stack">
      <button class="btn primary" data-action="bank-start" data-mode="new" ${newPool.length ? "" : "disabled"}>Làm câu mới<small>${newPool.length ? "Câu chọn ngẫu nhiên" : "Không còn câu nào"}</small></button>
      <button class="btn" data-action="bank-start" data-mode="wrong" ${wrongPool.length ? "" : "disabled"}>Làm lại câu sai<small>${st.wrong} câu</small></button>
      <button class="btn danger" data-action="bank-reset">Làm lại từ đầu</button>
      <button class="btn" data-action="back">← Quay lại</button>
    </div>
  </div>`;
}

function renderSummary() {
  const s = bsession;
  const bar = ctx.topBar({ title: `HSK ${s.level} · ${core.TABS.find((t) => t.id === s.tab).label}`, back: "level-back" });
  return `<div class="screen center">${bar}
    <div class="big-emoji">🎉</div><h2>Hoàn thành!</h2>
    <div class="stats">
      <div class="stat good"><b>${s.correct}</b>Đúng</div>
      <div class="stat bad"><b>${s.wrong}</b>Sai</div>
    </div>
    <p class="note">Đúng ${s.correct} / ${s.total} câu</p>
    <div class="stack">
      <button class="btn primary" data-action="bank-start" data-mode="${s.mode}">Làm tiếp</button>
      <button class="btn" data-action="level-back">Về danh sách</button>
    </div></div>`;
}

export function renderBankSummary() {
  stopAudio();
  return bsession ? renderSummary() : renderBankLevelFallback();
}

function renderBankLevelFallback() {
  ctx.setView({ name: "bank-level", level: ctx.getView().level });
  return renderBankLevel();
}

// ----- question screen -----
const audioBar = (name) => `<div class="audio-bar">
  <button class="btn primary" data-action="bank-play" data-clip="${name}">▶ Nghe</button>
  <button class="btn" data-action="bank-replay" data-clip="${name}">🔁 Nghe lại</button></div>`;

const imgTag = (name, cls = "") => `<img class="bank-img ${cls}" data-bimg="${name}" alt="" loading="lazy">`;

function optionButton(unit, q, o, a) {
  let cls = "opt";
  if (a) {
    if (o.key === q.answer) cls += " correct";
    else if (o.key === a.resp) cls += " wrong";
  }
  const tf = unit.type === "tf";
  const inner = tf
    ? `<span class="tfmark">${o.key}</span><span class="t">${o.key === "✓" ? "Đúng" : "Sai"}</span>`
    : `<span class="k">${esc(o.key)}</span>${o.image ? imgTag(o.image) : ""}${o.text ? `<span class="t">${esc(o.text)}</span>` : ""}`;
  return `<button class="${cls}${tf ? " tf" : ""}" data-action="bank-pick" data-qid="${esc(q.id)}" data-key="${esc(o.key)}" ${a ? "disabled" : ""}>${inner}</button>`;
}

function feedback(unit, q, a) {
  if (!a) return "";
  const wrongOrder = !a.ok && (unit.type === "order-words" || unit.type === "order-sentences");
  const answerLine = wrongOrder
    ? `<div class="right-answer"><span class="label">Đáp án:</span> <span class="zh">${esc(core.correctOrderText(unit, q))}</span></div>` : "";
  const override = wrongOrder && !a.overridden
    ? `<button class="btn small" data-action="bank-mine" data-qid="${esc(q.id)}">Câu của mình cũng đúng</button>` : "";
  const script = q.script ? `<div class="script"><span class="label">Nội dung nghe:</span><div class="zh">${esc(q.script)}</div></div>` : "";
  const vi = q.explain_vi ? `<div class="expl">${esc(q.explain_vi)}</div>` : "";
  const zh = q.explain_zh
    ? `<details class="expl-zh"><summary>Xem giải thích tiếng Trung</summary><div class="zh">${esc(q.explain_zh)}</div></details>` : "";
  return `<div class="fb ${a.ok ? "ok" : "no"}"><b>${a.ok ? "✅ Đúng" : "❌ Chưa đúng"}</b>${answerLine}${override}${script}${vi}${zh}</div>`;
}

function orderBlock(unit, q, a) {
  const picked = bsession.orders[q.id] || [];
  const opts = q.options;
  const sent = unit.type === "order-sentences";
  const label = (o) => `${sent ? `<b>${esc(o.key)}</b> ` : ""}${esc(o.text)}`;
  const line = picked.length
    ? picked.map((i) => `<button class="tile on" data-action="bank-tile" data-qid="${esc(q.id)}" data-i="${i}" ${a ? "disabled" : ""}>${label(opts[i])}</button>`).join("")
    : `<span class="ph">Chạm vào các mảnh bên dưới theo đúng thứ tự</span>`;
  const pool = opts.map((o, i) => picked.includes(i)
    ? `<button class="tile used" disabled>${label(o)}</button>`
    : `<button class="tile" data-action="bank-tile" data-qid="${esc(q.id)}" data-i="${i}" ${a ? "disabled" : ""}>${label(o)}</button>`).join("");
  return `<div class="answer-line ${a ? (a.ok ? "ok" : "no") : ""}" aria-label="Câu trả lời">${line}</div>
    <div class="tiles ${sent ? "long" : ""}">${pool}</div>
    <div class="order-actions">
      <button class="btn" data-action="bank-clear" data-qid="${esc(q.id)}" ${a || !picked.length ? "disabled" : ""}>Xóa</button>
      <button class="btn primary" data-action="bank-check" data-qid="${esc(q.id)}" ${a ? "disabled" : ""}>Kiểm tra</button>
    </div>`;
}

function questionBlock(unit, q, n) {
  const a = bsession.answers[q.id];
  const isOrder = unit.type === "order-words" || unit.type === "order-sentences";
  let body;
  if (isOrder) body = orderBlock(unit, q, a);
  else {
    const opts = unit.type === "tf" ? [{ key: "✓" }, { key: "✗" }] : (q.options || unit.context.sharedOptions || []);
    const hasImg = opts.some((o) => o.image);
    const cls = unit.type === "tf" ? "opt-grid two" : unit.type === "wordbank" ? "opt-grid words" : hasImg ? "opt-grid pics" : "opt-grid";
    body = `<div class="${cls}">${opts.map((o) => optionButton(unit, q, o, a)).join("")}</div>`;
  }
  return `<div class="qcard" data-qid="${esc(q.id)}">
    <div class="qnum">${n}</div>
    ${q.audio ? audioBar(q.audio) : ""}
    ${q.prompt ? `<div class="prompt zh">${esc(q.prompt)}</div>` : ""}
    ${body}
    ${feedback(unit, q, a)}
  </div>`;
}

export function renderBankQuestion() {
  const s = bsession;
  if (!s) return renderBankLevelFallback();
  const unit = s.units[s.unitIdx];
  const index = indexes[s.level];
  const first = s.doneBefore + 1;
  const last = s.doneBefore + unit.questions.length;
  const title = `Câu ${first}${last > first ? "–" + last : ""} / ${s.total}`;
  const ctxData = unit.context || {};
  const allDone = unit.questions.every((q) => s.answers[q.id]);
  const anyDone = unit.questions.some((q) => s.answers[q.id]);
  const shared = unit.type === "wordbank"
    ? `<div class="wordlist">${(ctxData.sharedOptions || []).map((o) => `<span class="wl"><b>${esc(o.key)}</b> ${esc(o.text)}</span>`).join("")}</div>` : "";
  const nextLabel = s.unitIdx === s.units.length - 1 ? "Xong" : "Tiếp";
  return `<div class="screen">
    ${ctx.topBar({ title, back: "exit-session" })}
    <div class="progress"><i style="width:${Math.round((s.doneBefore / s.total) * 100)}%"></i></div>
    <div class="source">Nguồn: ${esc(paperTitle(index, unit))}</div>
    ${ctxData.audio ? audioBar(ctxData.audio) : ""}
    ${ctxData.image ? imgTag(ctxData.image, "ctx") : ""}
    ${ctxData.text ? `<div class="passage zh">${esc(ctxData.text)}</div>` : ""}
    ${shared}
    ${anyDone && ctxData.script ? `<div class="script"><span class="label">Nội dung nghe:</span><div class="zh">${esc(ctxData.script)}</div></div>` : ""}
    ${unit.questions.map((q, i) => questionBlock(unit, q, first + i)).join("")}
    <div class="spacer"></div>
    <div class="actions"><button class="btn primary" data-action="bank-next" ${allDone ? "" : "disabled"}>${nextLabel}</button></div>
  </div>`;
}

// ---------- sessions ----------
function startSession(level, mode) {
  const units = unitsOf(level);
  const types = filters[tab];
  const pool = core.candidateUnits(units, { tab, types, mode, progress: progress() });
  if (!pool.length) { ctx.toast("Không còn câu nào để làm."); return; }
  const picked = core.takeUnits(ctx.shuffle(pool), store.getSettings().bankSize);
  bsession = {
    level, tab, mode, units: picked, unitIdx: 0, doneBefore: 0,
    total: picked.reduce((n, u) => n + u.questions.length, 0),
    correct: 0, wrong: 0, answers: {}, orders: {},
  };
  const v = ctx.getView();
  ctx.go({ name: "bank-q", level }, { replace: v.name === "bank-sum" });
}

function currentUnit() { return bsession.units[bsession.unitIdx]; }

function findQuestion(qid) {
  const unit = currentUnit();
  return { unit, q: unit.questions.find((x) => x.id === qid) };
}

function recordAnswer(unit, q, resp, ok) {
  bsession.answers[q.id] = { resp, ok, overridden: false };
  if (ok) bsession.correct++; else bsession.wrong++;
  store.setBankEntry(q.id, core.applyResult(progress()[q.id], ok));
}

function redraw() { ctx.render(); }

// ---------- events ----------
document.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-action^='bank-']");
  if (!el) return;
  const d = el.dataset;
  switch (d.action) {
    case "bank-open": ctx.go({ name: "bank" }); break;
    case "bank-retry": ready = load(); await ready; ctx.render(); break;
    case "bank-level": ctx.go({ name: "bank-level", level: Number(d.level) }); break;
    case "bank-tab": tab = d.tab; redraw(); break;
    case "bank-chip": {
      const list = filters[tab];
      const i = list.indexOf(d.type);
      if (i >= 0) list.splice(i, 1); else list.push(d.type);
      redraw();
      break;
    }
    case "bank-size": store.updateSettings({ bankSize: Number(d.value) }); redraw(); break;
    case "bank-start": startSession(ctx.getView().level, d.mode); break;
    case "bank-reset": {
      const level = ctx.getView().level;
      const label = core.TABS.find((t) => t.id === tab).label;
      const yes = await ctx.dialog({
        title: `Làm lại tab “${label}” từ đầu?`,
        message: "Kết quả các câu trong tab này sẽ bị xóa.",
        buttons: [{ label: "Xóa và làm lại", value: true, kind: "good" }, { label: "Hủy", value: null }],
      });
      if (yes) {
        const ids = unitsOf(level).filter((u) => u.skill === tab).flatMap((u) => u.questions.map((q) => q.id));
        store.resetBankIds(ids);
        ctx.toast(`Đã xóa kết quả tab ${label}`);
        redraw();
      }
      break;
    }
    case "bank-pick": {
      const { unit, q } = findQuestion(d.qid);
      if (!q || bsession.answers[q.id]) break;
      recordAnswer(unit, q, d.key, core.grade(unit, q, d.key));
      redraw();
      break;
    }
    case "bank-tile": {
      const { q } = findQuestion(d.qid);
      if (!q || bsession.answers[q.id]) break;
      const list = bsession.orders[q.id] || (bsession.orders[q.id] = []);
      const i = Number(d.i);
      const at = list.indexOf(i);
      if (at >= 0) list.splice(at, 1); else list.push(i);
      redraw();
      break;
    }
    case "bank-clear": {
      const { q } = findQuestion(d.qid);
      if (q && !bsession.answers[q.id]) { bsession.orders[q.id] = []; redraw(); }
      break;
    }
    case "bank-check": {
      const { unit, q } = findQuestion(d.qid);
      if (!q || bsession.answers[q.id]) break;
      const picked = bsession.orders[q.id] || [];
      if (picked.length < q.options.length) { ctx.toast("Hãy xếp đủ các mảnh trước khi kiểm tra."); break; }
      recordAnswer(unit, q, picked.slice(), core.grade(unit, q, picked));
      redraw();
      break;
    }
    case "bank-mine": {
      const { q } = findQuestion(d.qid);
      const a = q && bsession.answers[q.id];
      if (!a || a.ok) break;
      a.ok = true;
      a.overridden = true;
      bsession.wrong--;
      bsession.correct++;
      store.setBankEntry(q.id, core.applyOverride(progress()[q.id]));
      redraw();
      break;
    }
    case "bank-next": {
      const s = bsession;
      if (!s) break;
      stopAudio();
      s.doneBefore += currentUnit().questions.length;
      s.unitIdx++;
      if (s.unitIdx >= s.units.length) ctx.go({ name: "bank-sum", level: s.level }, { replace: true });
      else { redraw(); window.scrollTo(0, 0); }
      break;
    }
    case "bank-play": playClip(d.clip, false); break;
    case "bank-replay": playClip(d.clip, true); break;
    case "bank-lock": {
      await lock();
      ctx.toast("Đã khóa lại Luyện đề trên máy này");
      ctx.render();
      break;
    }
    case "bank-download": await downloadAll(); break;
  }
});

document.addEventListener("submit", async (e) => {
  if (e.target.id !== "bank-unlock-form") return;
  e.preventDefault();
  const pw = document.getElementById("bank-pw").value;
  const msg = document.getElementById("bank-msg");
  if (!pw) { msg.textContent = "Hãy nhập mật khẩu."; return; }
  const button = e.target.querySelector("button");
  button.disabled = true;
  button.textContent = "Đang mở khóa…";
  let ok = false;
  try { ok = await unlockWithPassword(pw); } catch (err) { ok = false; }
  if (ok) { ctx.render(); return; }
  button.disabled = false;
  button.textContent = "Mở khóa";
  msg.textContent = "Mật khẩu chưa đúng";
  msg.classList.add("error");
});

// ---------- settings ----------
export function settingsSection() {
  if (!meta || meta === "error" || !key) return "";
  return `<div class="section"><h2>Luyện đề</h2>
    <div class="stack">
      <button class="btn" data-action="bank-download">Tải toàn bộ đề về máy</button>
      <button class="btn" data-action="bank-lock">Khóa lại</button>
    </div>
    <p class="note">“Tải toàn bộ” để làm đề khi không có mạng. “Khóa lại” chỉ quên mật khẩu trên máy này, tiến độ vẫn được giữ.</p></div>`;
}

async function downloadAll() {
  const files = [];
  for (const level of meta.levels) {
    const index = await loadIndex(level);
    for (const [name, m] of Object.entries(index.media)) files.push({ url: `bank/hsk${level}/m/${name}.bin`, size: m.size });
  }
  const total = files.reduce((n, f) => n + f.size, 0);
  const mb = (total / 1e6).toFixed(1);
  const yes = await ctx.dialog({
    title: "Tải toàn bộ đề về máy?",
    message: `${files.length} tệp âm thanh và hình, khoảng ${mb} MB. Nên dùng Wi-Fi.`,
    buttons: [{ label: `Tải ${mb} MB`, value: true, kind: "primary" }, { label: "Hủy", value: null }],
  });
  if (!yes) return;
  let done = 0, failed = 0;
  const queue = files.slice();
  const worker = async () => {
    while (queue.length) {
      const f = queue.shift();
      try {
        const res = await fetch(f.url);
        if (!res.ok) throw new Error("HTTP " + res.status);
        await res.arrayBuffer();
      } catch (err) { failed++; }
      done++;
      if (done % 10 === 0) ctx.toast(`Đang tải… ${done} / ${files.length}`, 2000);
    }
  };
  await Promise.all([worker(), worker(), worker(), worker()]);
  ctx.toast(failed ? `Đã tải ${files.length - failed} / ${files.length} tệp. Thử lại sau để tải nốt.` : `Đã tải xong ${files.length} tệp (${mb} MB)`, 5000);
}

export function endSession() {
  stopAudio();
  bsession = null;
}
