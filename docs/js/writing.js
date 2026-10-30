// Writing practice: the learner writes each Han character of a word, one at a time, with Hanzi Writer
// (vendored in vendor/, loaded on first use) and the stroke data in hanzi/{char}.json (cached by the service worker).
const HAN = /[㐀-䶿一-鿿豈-﫿\u{20000}-\u{2fa1f}]/u;
const AREA_MAX = 300;
const NEXT_DELAY = 500; // pause after a finished character before the next one

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

let libPromise = null;
function loadLib() {
  if (window.HanziWriter) return Promise.resolve(window.HanziWriter);
  if (!libPromise) {
    libPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "vendor/hanzi-writer.min.js";
      s.onload = () => resolve(window.HanziWriter);
      s.onerror = () => { libPromise = null; reject(new Error("cannot load hanzi-writer")); };
      document.head.appendChild(s);
    });
  }
  return libPromise;
}

const dataCache = new Map();
/** Resolves { data } for a character, { missing: true } when there is no data file, { offline: true } when it can't be fetched. */
async function fetchChar(ch) {
  if (dataCache.has(ch)) return { data: dataCache.get(ch) };
  try {
    const res = await fetch(`hanzi/${encodeURIComponent(ch)}.json`);
    if (res.status === 404) return { missing: true };
    if (!res.ok) return { offline: true };
    const data = await res.json();
    dataCache.set(ch, data);
    return { data };
  } catch (e) {
    return { offline: true };
  }
}

const cssVar = (name, fallback) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;

let openWriters = 0;
const setWritingMode = (on) => {
  openWriters += on ? 1 : -1;
  document.documentElement.classList.toggle("writing-open", openWriters > 0); // stops pull-to-refresh / overscroll mid-stroke
};

/**
 * Mount the writing UI for `word` inside `root`.
 *   opts.outline          start with the faint outline shown
 *   opts.onOutlineChange  called with the new value when the learner toggles it
 *   opts.onFinish         called once after the last character with { mistakes, skipped, noData }
 * Returns { destroy() }.
 */
export function mountWriter(root, word, opts = {}) {
  const chars = [...word.hanzi];
  const quiz = chars.map((c, i) => (HAN.test(c) ? i : -1)).filter((i) => i >= 0);
  const result = { mistakes: 0, skipped: 0, noData: 0 };
  const size = Math.min(Math.round(window.innerWidth * 0.8), AREA_MAX);
  let outline = !!opts.outline;
  let step = 0;
  let token = 0; // bumped on every (re)build so late async work from an old character is ignored
  let busy = false; // an animation or the pause after a finished character is running
  let staticChar = false; // the current character can't be quizzed (no data)
  let finished = false;
  let destroyed = false;
  let writer = null;
  let timer = null;

  root.innerHTML = `
    <div class="wr-boxes" aria-label="Các chữ cần viết">${chars.map((c, i) => (HAN.test(c)
      ? `<span class="wr-box" data-i="${i}"></span>` : `<span class="wr-text">${esc(c)}</span>`)).join("")}</div>
    <div class="wr-area" style="width:${size}px;height:${size}px">
      <svg class="wr-grid" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <line x1="50" y1="0" x2="50" y2="100"/><line x1="0" y1="50" x2="100" y2="50"/>
        <line x1="0" y1="0" x2="100" y2="100"/><line x1="100" y1="0" x2="0" y2="100"/>
      </svg>
      <div class="wr-canvas"></div>
    </div>
    <p class="wr-note" hidden></p>
    <div class="wr-actions">
      <button class="btn" data-wr="animate">Xem cách viết</button>
      <button class="btn" data-wr="outline"></button>
      <button class="btn" data-wr="redo">Viết lại</button>
      <button class="btn" data-wr="skip">Bỏ qua chữ này</button>
    </div>`;
  const $canvas = root.querySelector(".wr-canvas");
  const $note = root.querySelector(".wr-note");
  const $outline = root.querySelector('[data-wr="outline"]');
  const $skip = root.querySelector('[data-wr="skip"]');
  const boxes = [...root.querySelectorAll(".wr-box")];
  const boxOf = (i) => boxes.find((b) => Number(b.dataset.i) === i);
  const labelOutline = () => { $outline.textContent = outline ? "Ẩn chữ mờ" : "Hiện chữ mờ"; };
  labelOutline();
  setWritingMode(true);

  // while an animation or the pause after a character runs, the buttons that would interfere are disabled
  function setBusy(on) {
    busy = on;
    for (const b of root.querySelectorAll('[data-wr="animate"], [data-wr="redo"], [data-wr="skip"]')) b.disabled = on;
  }

  function mark(current) {
    for (const b of boxes) b.classList.toggle("current", Number(b.dataset.i) === current);
  }

  function fillBox(i) {
    const b = boxOf(i);
    if (b) { b.textContent = chars[i]; b.classList.add("done"); }
  }

  function later(fn, ms) {
    clearTimeout(timer);
    timer = setTimeout(() => { if (!destroyed) fn(); }, ms);
  }

  function next() {
    step++;
    showChar();
  }

  function finish() {
    finished = true;
    setBusy(true);
    mark(-1);
    root.querySelectorAll("[data-wr]").forEach((b) => { b.disabled = true; });
    if (opts.onFinish) opts.onFinish({ ...result });
  }

  async function showChar() {
    const my = ++token;
    clearTimeout(timer);
    writer = null;
    setBusy(false);
    staticChar = false;
    $skip.textContent = "Bỏ qua chữ này";
    $note.hidden = true;
    $canvas.innerHTML = "";
    if (step >= quiz.length) { finish(); return; }
    const i = quiz[step];
    const ch = chars[i];
    mark(i);
    let HW = null;
    let res;
    try {
      [HW, res] = await Promise.all([loadLib(), fetchChar(ch)]);
    } catch (e) {
      res = { offline: true };
    }
    if (destroyed || my !== token) return;
    if (!HW || !res.data) {
      staticChar = true;
      $skip.textContent = "Tiếp";
      $canvas.innerHTML = `<div class="wr-static">${esc(ch)}</div>`;
      $note.textContent = res.missing
        ? "Chưa có dữ liệu nét cho chữ này."
        : "Không tải được nét chữ này. Hãy bật mạng một lần để tải, rồi bấm “Viết lại”.";
      $note.hidden = false;
      return;
    }
    writer = HW.create($canvas, ch, {
      width: size,
      height: size,
      padding: 14,
      showCharacter: false,
      showOutline: outline,
      charDataLoader: (_c, onLoad) => onLoad(res.data),
      strokeColor: cssVar("--text", "#1c2233"),
      outlineColor: cssVar("--wr-outline", "#b9c2d9"),
      drawingColor: cssVar("--primary", "#2457c5"),
      highlightColor: cssVar("--wr-hint", "#e08a00"),
      highlightCompleteColor: cssVar("--good", "#1f8a52"),
      drawingWidth: 8,
      strokeAnimationSpeed: 1.2,
      delayBetweenStrokes: 250,
    });
    writer.quiz({
      showHintAfterMisses: 3,
      highlightOnComplete: true,
      leniency: 1,
      onComplete: (summary) => {
        if (destroyed || my !== token) return;
        setBusy(true);
        result.mistakes += summary.totalMistakes;
        fillBox(i);
        later(next, NEXT_DELAY);
      },
    });
  }

  function onClick(e) {
    const btn = e.target.closest("[data-wr]");
    if (!btn || btn.disabled || finished) return;
    const action = btn.dataset.wr;
    if (action === "outline") {
      outline = !outline;
      labelOutline();
      if (opts.onOutlineChange) opts.onOutlineChange(outline);
      if (writer) { if (outline) writer.showOutline(); else writer.hideOutline(); }
      return;
    }
    if (busy) return;
    const i = quiz[step];
    if (action === "redo") {
      showChar();
    } else if (action === "animate") {
      if (!writer) return;
      setBusy(true);
      const my = token;
      writer.cancelQuiz();
      writer.animateCharacter({ onComplete: () => { if (!destroyed && my === token) showChar(); } });
    } else if (action === "skip") {
      setBusy(true);
      if (staticChar) {
        result.noData++;
        fillBox(i);
        later(next, 200);
        return;
      }
      result.skipped++;
      if (writer) { writer.cancelQuiz(); writer.showCharacter(); }
      fillBox(i);
      later(next, NEXT_DELAY + 300);
    }
  }
  root.addEventListener("click", onClick);

  showChar();

  return {
    destroy() {
      if (destroyed) return;
      destroyed = true;
      clearTimeout(timer);
      root.removeEventListener("click", onClick);
      try { if (writer) writer.cancelQuiz(); } catch (e) { /* already gone */ }
      setWritingMode(false);
    },
  };
}
