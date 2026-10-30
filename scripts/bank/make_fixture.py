"""Create the made-up test bank (specs/mock-tests.md section 9). Never real content.

  python scripts/bank/make_fixture.py

Writes scripts/fixtures/papers/hsk4-fixture-1/ (invented questions, one generated image, two generated tone clips)
and encrypts it with the public test password into scripts/fixtures/bank/. Tests serve that folder as /bank/.
"""
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bank import build  # noqa: E402
from paths import ROOT  # noqa: E402

TEST_PASSWORD = "test-password"
FIX = ROOT / "scripts" / "fixtures"
PID = "hsk4-fixture-1"


def tone_mp3(path: Path, hz: int, seconds: float = 0.8):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "t.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            frames = b"".join(int(9000 * math.sin(2 * math.pi * hz * i / 16000)).to_bytes(2, "little", signed=True) for i in range(int(16000 * seconds)))
            w.writeframes(frames)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-b:a", "32k", str(path)], check=True)


def image_webp(path: Path):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (240, 160), "#fff3cf")
    d = ImageDraw.Draw(im)
    d.ellipse((60, 30, 180, 130), fill="#e8553a", outline="#7a1d0d", width=4)
    d.rectangle((20, 120, 220, 150), fill="#2457c5")
    im.save(path, "WEBP", quality=70)


def q(n, prompt, options, answer, **extra):
    return {"id": f"{PID}-{n}", "prompt": prompt, "options": options, "answer": answer, "audio": None, "script": "", **extra}


def opts(*texts):
    return [{"key": k, "text": t} for k, t in zip("ABCD", texts)]


def papers_json():
    pic = [{"key": "A", "text": "", "image": "img/cat.webp"}, {"key": "B", "text": "", "image": "img/cat.webp"}]
    return {
        "paper": {"id": PID, "level": 4, "examVersion": "fixture", "title": "Đề thử"},
        "units": [
            {"id": f"{PID}-N1", "skill": "nghe", "type": "tf", "context": {},
             "questions": [q(1, "我家有一只小猫。", None, "✓", audio="clips/a.mp3", script="我家有一只小猫。",
                             explain_zh="录音里说家里有一只猫。", explain_vi="Bản ghi nói nhà có một con mèo.")]},
            {"id": f"{PID}-N2", "skill": "nghe", "type": "tf", "context": {},
             "questions": [q(2, "今天天气不好。", None, "✗", audio="clips/b.mp3", script="今天天气很好。",
                             explain_vi="Bản ghi nói thời tiết rất tốt.")]},
            {"id": f"{PID}-N3", "skill": "nghe", "type": "choice", "context": {},
             "questions": [q(3, "", opts("去商店", "去公园", "回家", "看电影"), "B", audio="clips/a.mp3",
                             script="女：明天你想做什么？男：我想去公园。", explain_zh="男的想去公园。", explain_vi="Người nam muốn đi công viên.")]},
            {"id": f"{PID}-N4", "skill": "nghe", "type": "choice", "context": {"audio": "clips/b.mp3"},
             "questions": [q(4, "他在做什么？", opts("看书", "写字", "做饭", "睡觉"), "A", script="他正在看一本书。"),
                           q(5, "书怎么样？", opts("很贵", "很有意思", "很旧", "很小"), "B", script="这本书很有意思。")]},
            {"id": f"{PID}-D1", "skill": "doc", "type": "wordbank",
             "context": {"sharedOptions": [{"key": "A", "text": "喜欢"}, {"key": "B", "text": "快乐"}, {"key": "C", "text": "已经"}, {"key": "D", "text": "因为"}]},
             "questions": [q(6, "我 ( ) 吃苹果。", None, "A", explain_vi="喜欢 = thích."),
                           q(7, "他 ( ) 走了。", None, "C"),
                           q(8, "( ) 下雨，我没出门。", None, "D")]},
            {"id": f"{PID}-D2", "skill": "doc", "type": "choice",
             "context": {"text": "小明有一只小狗。每天早上，他带小狗去河边玩。小狗很喜欢水。"},
             "questions": [q(9, "小明什么时候带小狗出去？", opts("早上", "中午", "晚上", "下午"), "A", explain_vi="Đoạn văn nói “每天早上”."),
                           q(10, "小狗喜欢什么？", opts("饭", "水", "书", "车"), "B")]},
            {"id": f"{PID}-D3", "skill": "doc", "type": "choice", "context": {"image": "img/cat.webp"},
             "questions": [q(11, "图片里有什么颜色？", [{"key": "A", "text": "红色和蓝色"}, {"key": "B", "text": "绿色"}], "A")]},
            {"id": f"{PID}-D4", "skill": "doc", "type": "choice", "context": {},
             "questions": [q(12, "哪一张图是圆的？", pic, "A")]},
            {"id": f"{PID}-S1", "skill": "sapxep", "type": "order-sentences", "context": {},
             "questions": [q(13, "", [{"key": "A", "text": "所以他今天没去上班"}, {"key": "B", "text": "小王昨天病了"}, {"key": "C", "text": "现在他好多了"}], "BAC",
                             explain_vi="Trình tự thời gian: bệnh → nghỉ làm → đỡ hơn.")]},
            {"id": f"{PID}-S2", "skill": "sapxep", "type": "order-sentences", "context": {},
             "questions": [q(14, "", [{"key": "A", "text": "我们一起去吃饭吧"}, {"key": "B", "text": "已经十二点了"}, {"key": "C", "text": "你饿不饿"}], "BCA")]},
            {"id": f"{PID}-S3", "skill": "sapxep", "type": "order-words", "context": {},
             "questions": [q(15, "", [{"key": "1", "text": "我"}, {"key": "2", "text": "喜欢"}, {"key": "3", "text": "吃"}, {"key": "4", "text": "苹果"}], "我喜欢吃苹果。",
                             explain_vi="Chủ ngữ + động từ + tân ngữ.")]},
            {"id": f"{PID}-S4", "skill": "sapxep", "type": "order-words", "context": {},
             "questions": [q(16, "", [{"key": "1", "text": "明天"}, {"key": "2", "text": "我们"}, {"key": "3", "text": "去公园"}], "明天我们去公园。",
                             alsoAccept=["我们明天去公园。"])]},
        ],
    }


def main():
    work = FIX / "papers"
    d = work / PID
    (d / "clips").mkdir(parents=True, exist_ok=True)
    (d / "img").mkdir(exist_ok=True)
    tone_mp3(d / "clips" / "a.mp3", 440)
    tone_mp3(d / "clips" / "b.mp3", 660)
    image_webp(d / "img" / "cat.webp")
    (d / "questions.json").write_text(json.dumps(papers_json(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    r = build(work, FIX / "bank", TEST_PASSWORD)
    print("fixture bank:", r["levels"], r["write"])


if __name__ == "__main__":
    main()
