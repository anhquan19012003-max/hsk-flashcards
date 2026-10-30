// Unit test of docs/js/strokematch.js on every character used by HSK1-5: strokes drawn with noise, in a shuffled
// order, must all be accepted; a clearly wrong line and a backwards stroke must be rejected.
import { readFileSync, readdirSync } from "node:fs";
import { bestMatch } from "../docs/js/strokematch.js";

let seed = 12345;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);
const dir = new URL("../docs/hanzi/", import.meta.url);
let chars = 0, strokes = 0, failedChars = [], wrongAccepted = 0, wrongTried = 0, backAccepted = 0, backTried = 0;

const jitter = (median, amp) => {
  // dense polyline, shifted as a whole and with a slow wobble, like a finger (no high-frequency noise)
  const pts = [];
  for (let i = 1; i < median.length; i++) {
    const n = Math.max(1, Math.round(Math.hypot(median[i][0] - median[i - 1][0], median[i][1] - median[i - 1][1]) / 8));
    for (let k = 0; k < n; k++) {
      const t = k / n;
      pts.push([median[i - 1][0] + (median[i][0] - median[i - 1][0]) * t, median[i - 1][1] + (median[i][1] - median[i - 1][1]) * t]);
    }
  }
  pts.push(median[median.length - 1]);
  const ox = (rnd() - 0.5) * 2 * amp, oy = (rnd() - 0.5) * 2 * amp, ph = rnd() * 6;
  return pts.map(([x, y], i) => [x + ox + Math.sin(i / 5 + ph) * amp * 0.3, y + oy + Math.cos(i / 5 + ph) * amp * 0.3]);
};

for (const f of readdirSync(dir)) {
  const data = JSON.parse(readFileSync(new URL(f, dir), "utf8"));
  const m = data.medians;
  chars++;
  strokes += m.length;
  const order = m.map((_, i) => i).sort(() => rnd() - 0.5);
  const used = new Set();
  let ok = true;
  for (const i of order) {
    const k = bestMatch(jitter(m[i], 40), m, used);
    if (k < 0) { ok = false; break; }
    used.add(k);
  }
  if (!ok || used.size !== m.length) failedChars.push(f);
  // a line that is nowhere near any stroke of this character (a diagonal across a corner)
  wrongTried++;
  if (bestMatch([[0, -100], [200, 100], [400, 300]], m.filter((s) => s[0][0] > 300 && s[0][1] > 300), new Set()) >= 0) wrongAccepted++;
  // backwards stroke of a long stroke
  const long = m.findIndex((s) => Math.hypot(s[0][0] - s[s.length - 1][0], s[0][1] - s[s.length - 1][1]) > 400);
  if (long >= 0) { backTried++; if (bestMatch(jitter([...m[long]].reverse(), 20), [m[long]], new Set()) >= 0) backAccepted++; }
}
console.log(`${chars} characters, ${strokes} strokes; failed (noisy, shuffled order): ${failedChars.length}`, failedChars.slice(0, 10));
console.log(`wrong line accepted: ${wrongAccepted}/${wrongTried}; backwards stroke accepted: ${backAccepted}/${backTried}`);
process.exit(failedChars.length || wrongAccepted || backAccepted ? 1 : 0);
