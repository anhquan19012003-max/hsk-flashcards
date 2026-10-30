// Order-free stroke matching for writing practice. A drawn stroke is compared with the centre line ("median") of
// every stroke of the character that has not been written yet; the closest one that is close enough is accepted.
// Points are in the character data's coordinate system (a 1024-wide square, y pointing up): [x, y].
export const MATCH_DISTANCE = 110; // max average distance between the drawn line and a stroke's centre line
const END_FACTOR = 1.5; // the start and the end of the stroke may be a bit further off than the average
const SAMPLES = 24;

const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

export function pathLength(pts) {
  let total = 0;
  for (let i = 1; i < pts.length; i++) total += dist(pts[i - 1], pts[i]);
  return total;
}

/** `n` points spread evenly along the polyline (a single point or a zero-length line repeats that point). */
export function resample(pts, n) {
  const total = pathLength(pts);
  if (pts.length < 2 || total < 1e-6) return Array.from({ length: n }, () => pts[0]);
  const out = [pts[0]];
  const step = total / (n - 1);
  let seg = 1;
  let covered = 0; // length of the polyline before pts[seg - 1]
  for (let k = 1; k < n - 1; k++) {
    const target = k * step;
    while (seg < pts.length - 1 && covered + dist(pts[seg - 1], pts[seg]) < target) {
      covered += dist(pts[seg - 1], pts[seg]);
      seg++;
    }
    const a = pts[seg - 1];
    const b = pts[seg];
    const len = dist(a, b) || 1;
    const t = Math.min(1, Math.max(0, (target - covered) / len));
    out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]);
  }
  out.push(pts[pts.length - 1]);
  return out;
}

/** How far the drawn line is from one stroke's centre line, or null when it is not a match. */
export function strokeDistance(drawn, median) {
  if (!drawn.length || !median.length) return null;
  const d = resample(drawn, SAMPLES);
  const m = resample(median, SAMPLES);
  let sum = 0;
  for (let i = 0; i < SAMPLES; i++) sum += dist(d[i], m[i]);
  const mean = sum / SAMPLES;
  const ends = Math.max(dist(d[0], m[0]), dist(d[SAMPLES - 1], m[SAMPLES - 1]));
  const lenD = pathLength(drawn);
  const lenM = pathLength(median);
  const lengthOk = lenM > 150 ? lenD > lenM * 0.45 && lenD < lenM * 2.2 : Math.abs(lenD - lenM) < 220;
  if (mean >= MATCH_DISTANCE || ends >= MATCH_DISTANCE * END_FACTOR || !lengthOk) return null;
  return mean;
}

/** Index of the closest not-yet-used stroke the drawn line matches, or -1. `used` is a Set of stroke indices. */
export function bestMatch(drawn, medians, used) {
  let best = -1;
  let bestDist = Infinity;
  medians.forEach((median, i) => {
    if (used.has(i)) return;
    const d = strokeDistance(drawn, median);
    if (d !== null && d < bestDist) { best = i; bestDist = d; }
  });
  return best;
}
