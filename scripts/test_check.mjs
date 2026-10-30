import { checkAnswer, canon } from "../docs/js/check.js";
let fail = 0;
const t = (input, accept, want, note) => {
  const got = checkAnswer(input, accept);
  if (got !== want) { fail++; console.log("FAIL", JSON.stringify(input), accept, "want", want, "got", got, note || ""); }
};
const ai = ["爱好", "àihào", "aihao"];
t("爱好", ai, true); t("àihào", ai, true); t("AIHAO", ai, true); t("ai hao", ai, true); t("ài hào", ai, true);
t("ai4hao4", ai, true); t("ai4hao3", ai, false, "wrong tone number"); t("àihǎo", ai, false, "wrong tone mark");
t("ài'hào", ai, true); t("ài-hào", ai, true); t("ài·hào", ai, true); t("(ài)hào", ai, true);
t("ai", ai, false); t("", ai, false); t("爱", ai, false);
const nv = ["女", "nǚ", "nu"];
t("nǚ", nv, true); t("nv3", nv, true); t("nü3", nv, true); t("nu3", nv, true); t("nv", nv, true); t("nü", nv, true); t("nu", nv, true); t("nǔ", nv, true, "u for ü with right tone"); t("nǜ", nv, false);
const lv = ["绿", "lǜ", "lü"];
t("lv4", lv, true); t("lǜ", lv, true); t("lu4", lv, true); t("lv3", lv, false); t("lv", lv, true);
const yy = ["有(一)些", "yǒu(yì)xiē", "youxie"];
t("有一些", yy, true); t("有些", yy, true); t("yǒuyìxiē", yy, true); t("yǒuxiē", yy, true); t("you3yi4xie1", yy, true); t("youyixie", yy, true);
// tone number placement
const cases = [["hao3","hǎo"],["xue2","xué"],["liu2","liú"],["gui4","guì"],["dou1","dōu"],["lve4","lüè"],["ma5","ma"],["a1","ā"]];
for (const [a,b] of cases) { if (canon(a) !== canon(b)) { fail++; console.log("FAIL canon", a, canon(a), b, canon(b)); } }
t("ma", ["吗","ma"], true); t("ma5", ["吗","ma"], true);
t("shuì jiào", ["睡觉","shuìjiào","shuijiao"], true); t("shui4jiao4", ["睡觉","shuìjiào"], true);
t("Xīān", ["西安","Xī'ān"], true, "apostrophes are ignored"); t("xi'an", ["西安","Xī'ān"], true); t("xian", ["西安","Xī'ān"], true);
console.log(fail ? fail + " FAILED" : "all check.js tests passed");
