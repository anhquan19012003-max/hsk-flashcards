// Pieces shared by the flash cards (app.js) and the Trắc nghiệm quiz (quiz.js): escaping and the highlighted example sentence.
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** The example sentence as HTML with the target word (or the two halves of a separable verb) marked. */
export function highlight(zh, hanzi) {
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

/** The card back in a compact form (hanzi + 🔊, pinyin, Hán Việt, từ loại, nghĩa, example). `actions` names the speak buttons' data-action values. */
export function wordCardHtml(word, { speakWord, speakSentence, extraClass = "" }) {
  const ex = word.example;
  return `<div class="card ${extraClass}">
      <div class="hz-row"><span class="hanzi-mid">${esc(word.hanzi)}</span>
        <button class="speak" data-action="${speakWord}" aria-label="Nghe phát âm">🔊</button></div>
      <div class="pinyin">${esc(word.pinyin)}</div>
      ${word.hanviet ? `<div class="info"><span class="label">Hán Việt:</span> ${esc(word.hanviet)}</div>` : ""}
      ${word.pos ? `<div class="info"><span class="label">Từ loại:</span> ${esc(word.pos)}</div>` : ""}
      <div class="meaning">${esc(word.meaning)}</div>
      ${ex && ex.zh ? `<div class="example">
          <div class="row"><div class="zh">${highlight(ex.zh, word.hanzi)}</div>
            <button class="speak" data-action="${speakSentence}" aria-label="Nghe câu ví dụ">🔊</button></div>
          ${ex.pinyin ? `<div class="py">${esc(ex.pinyin)}</div>` : ""}
          ${ex.vi ? `<div class="vi">${esc(ex.vi)}</div>` : ""}
        </div>` : ""}
    </div>`;
}
