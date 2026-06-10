# -*- coding: utf-8 -*-
"""
Do toc do OmniVoice: so sanh BAN WINDOWS in-process vs BAN SERVER (WSL/Linux).

Cach dung:
  # 1) Do ban Windows in-process (chay trong .venv Windows):
  python benchmark.py

  # 2) Do ban server (vd server WSL dang chay o cong 8090):
  python benchmark.py --url http://127.0.0.1:8090

Ket qua in ra: thoi gian tao moi cau, do dai audio, RTF (real-time factor:
cang nho cang nhanh; <1 = nhanh hon thoi gian thuc), va trung binh.
Cau warmup khong tinh gio (de loai phan torch.compile bien dich lan dau).
"""
import argparse
import io
import json
import sys
import time
import urllib.request

import soundfile as sf

# Bo cau test: tron cau CUC NGAN (de bay nuot tu), cau co so, va cau dai.
SENTENCES = [
    "Được rồi.",
    "Mẹ ơi.",
    "Đúng vậy.",
    "Cảm ơn anh rất nhiều.",
    "Hôm nay trời đẹp, mình đi dạo một chút nhé.",
    "Giảm giá năm mươi phần trăm trong ba ngày tới.",
    "Tôi vốn là một người thích tự do và ánh nắng, nhưng dạo này lại thấy khá u uất.",
]


def via_server(url, text):
    body = json.dumps({"text": text, "language": "vietnamese"}).encode("utf-8")
    req = urllib.request.Request(url.rstrip("/") + "/generate", data=body,
                                 headers={"content-type": "application/json"})
    t0 = time.time()
    wav = urllib.request.urlopen(req, timeout=600).read()
    dt = time.time() - t0
    a, sr = sf.read(io.BytesIO(wav))
    return dt, len(a) / sr


def via_inproc(text):
    import tts_engine as engine
    t0 = time.time()
    a, sr = engine.generate(text, language="vietnamese")
    dt = time.time() - t0
    return dt, len(a) / sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="URL server (vd http://127.0.0.1:8090). Bo trong = in-process Windows.")
    ap.add_argument("--runs", type=int, default=1, help="So vong lap qua bo cau (mac dinh 1).")
    args = ap.parse_args()

    mode = ("SERVER " + args.url) if args.url else "IN-PROCESS (Windows)"
    gen = (lambda t: via_server(args.url, t)) if args.url else via_inproc

    print(f"== Che do do: {mode} ==")
    print("Warmup (khong tinh gio, co the lau neu bat torch.compile)...")
    try:
        gen("Xin chào, đây là bước khởi động.")
    except Exception as e:
        print("Loi warmup:", e)
        sys.exit(1)

    total_gen = 0.0
    total_audio = 0.0
    n = 0
    print("-" * 64)
    for _ in range(args.runs):
        for s in SENTENCES:
            try:
                dt, dur = gen(s)
            except Exception as e:
                print(f"  [LOI] {s[:40]}: {e}")
                continue
            total_gen += dt
            total_audio += dur
            n += 1
            print(f"  {dt:6.2f}s tao | {dur:5.2f}s audio | RTF {dt / max(dur, 1e-6):4.2f} | {s[:42]}")
    print("-" * 64)
    if n:
        print(f"So cau:               {n}")
        print(f"Tong thoi gian tao:   {total_gen:.2f}s")
        print(f"Tong audio sinh ra:   {total_audio:.2f}s")
        print(f"RTF trung binh:       {total_gen / max(total_audio, 1e-6):.3f}  "
              f"(cang nho cang nhanh; <1 = nhanh hon thoi gian thuc)")
        print(f"TB moi cau:           {total_gen / n:.2f}s")


if __name__ == "__main__":
    main()
