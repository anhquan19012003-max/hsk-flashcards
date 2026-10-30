// Text-to-speech with the browser's built-in speechSynthesis (zh-CN). Speech only ever starts from a tap.
const RATES = {
  normal: { word: 0.9, sentence: 0.8 },
  slow: { word: 0.7, sentence: 0.6 },
};

let voices = [];
let zhVoice = null;

const synth = "speechSynthesis" in window ? window.speechSynthesis : null;

function pickVoice() {
  if (!synth) return;
  voices = synth.getVoices();
  const lang = (v) => v.lang.replace("_", "-").toLowerCase();
  zhVoice =
    voices.find((v) => lang(v) === "zh-cn") ||
    voices.find((v) => lang(v).startsWith("zh-cn") || lang(v).startsWith("cmn-cn")) ||
    voices.find((v) => lang(v).startsWith("zh") || lang(v).startsWith("cmn")) ||
    null;
}

export function initSpeech() {
  if (!synth) return;
  pickVoice();
  if (typeof synth.addEventListener === "function") synth.addEventListener("voiceschanged", pickVoice);
  else synth.onvoiceschanged = pickVoice;
}

/**
 * Speak Chinese text. `kind` is "word" or "sentence"; `speed` is "normal" or "slow".
 * `onMissing` is called when the device has no Chinese voice.
 */
export function speak(text, kind, speed, onMissing) {
  if (!synth) { onMissing(); return; }
  if (!zhVoice) pickVoice();
  if (voices.length > 0 && !zhVoice) { onMissing(); return; }
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/[()（）]/g, ""));
  u.lang = "zh-CN";
  if (zhVoice) u.voice = zhVoice;
  u.rate = (RATES[speed] || RATES.normal)[kind === "sentence" ? "sentence" : "word"];
  u.onerror = (e) => {
    if (["language-unavailable", "voice-unavailable", "synthesis-unavailable"].includes(e.error)) onMissing();
  };
  synth.speak(u);
}
