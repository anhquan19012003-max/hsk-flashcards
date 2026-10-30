// Text-to-speech with the browser's built-in speechSynthesis (zh-CN). Speech only ever starts from a tap.
const RATES = {
  normal: { word: 0.9, sentence: 0.8 },
  slow: { word: 0.7, sentence: 0.6 },
};

let voices = [];
let zhVoice = null;
let preferredUri = "";
let onVoicesChanged = () => {};

const synth = "speechSynthesis" in window ? window.speechSynthesis : null;

const lang = (v) => v.lang.replace("_", "-").toLowerCase();
const isChinese = (v) => lang(v).startsWith("zh") || lang(v).startsWith("cmn");

function pickVoice() {
  if (!synth) return;
  voices = synth.getVoices();
  zhVoice =
    voices.find((v) => v.voiceURI === preferredUri && isChinese(v)) ||
    voices.find((v) => lang(v) === "zh-cn") ||
    voices.find((v) => lang(v).startsWith("zh-cn") || lang(v).startsWith("cmn-cn")) ||
    voices.find(isChinese) ||
    null;
}

function handleVoicesChanged() {
  pickVoice();
  onVoicesChanged();
}

/** `voiceUri` is the voice saved in settings ("" = automatic); `onChange` fires when the device's voice list changes. */
export function initSpeech(voiceUri = "", onChange = () => {}) {
  preferredUri = voiceUri;
  onVoicesChanged = onChange;
  if (!synth) return;
  pickVoice();
  if (typeof synth.addEventListener === "function") synth.addEventListener("voiceschanged", handleVoicesChanged);
  else synth.onvoiceschanged = handleVoicesChanged;
}

/** Chinese voices on this device, as [{ uri, name, lang, active }]. */
export function listVoices() {
  if (!synth) return [];
  if (voices.length === 0) pickVoice();
  return voices.filter(isChinese).map((v) => ({ uri: v.voiceURI, name: v.name, lang: v.lang, active: v === zhVoice }));
}

/** Is there a Chinese voice on this device? (The quiz hides its listening questions without one.) */
export function hasChineseVoice() {
  return listVoices().length > 0;
}

/** Use this voice from now on ("" = automatic). */
export function setVoice(uri) {
  preferredUri = uri;
  pickVoice();
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
