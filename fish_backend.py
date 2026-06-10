# -*- coding: utf-8 -*-
"""
Backend Fish Speech (OpenAudio S1) cho GUI hop nhat.

GUI noi chuyen voi server Fish Speech qua HTTP (cong 8080, body msgpack) - dung
DUNG dinh dang request ma tool D:\\Tool_voice dang dung. KHONG can import goi
fish_speech: chi dung ormsgpack de dong goi 1 dict cung ten truong.

- start(): neu 8080 da chay -> dung lai; chua thi tu bat server Windows tu
  thu muc fish_speech_native (dung venv cua no). Khong bat duoc -> bao nguoi dung.
- generate(): POST /v1/tts -> tra ve (mono float32 numpy, sr).
- stop(): tat server neu CHINH ta da bat.
"""
from __future__ import annotations

import io
import os
import socket
import subprocess
import sys
import time
import urllib.request

import numpy as np

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

# Thu muc tool Fish Speech (sua lai neu ban dat o cho khac)
FISH_DIR = r"D:\Tool_voice\fish_speech_native"
FISH_PORT = 8080


class FishServer:
    def __init__(self, port=FISH_PORT, fish_dir=FISH_DIR, log=print):
        self.port = port
        self.fish_dir = fish_dir
        self.log = log
        self.proc = None
        self.url = f"http://127.0.0.1:{port}"

    # ---- trang thai ----
    def _port_open(self):
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1.5):
                return True
        except OSError:
            return False

    # ---- khoi dong ----
    def start(self, stop_check=None, wait_sec=600):
        if self._port_open():
            self.log(f"Server Fish Speech da chay san ({self.url}).")
            return True

        venv_py = os.path.join(self.fish_dir, ".venv", "Scripts", "python.exe")
        if not os.path.isfile(venv_py):
            venv_py = sys.executable  # du phong: python hien tai
        if not os.path.isdir(self.fish_dir):
            self.log(f"[LOI] Khong thay thu muc Fish Speech: {self.fish_dir}")
            self.log("    -> Hay mo server Fish Speech bang tool cua ban truoc, roi thu lai.")
            return False

        cmd = [venv_py, "-m", "tools.api_server",
               "--listen", f"0.0.0.0:{self.port}",
               "--llama-checkpoint-path", "checkpoints/openaudio-s1-mini",
               "--decoder-checkpoint-path", "checkpoints/openaudio-s1-mini/codec.pth",
               "--decoder-config-name", "modded_dac_vq", "--half"]
        self.log("Dang khoi dong server Fish Speech (nap model ~30s, lan dau co the lau)...")
        try:
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            self.proc = subprocess.Popen(
                cmd, cwd=self.fish_dir, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            self.log(f"[LOI] Khong bat duoc server Fish Speech: {e}")
            self.log("    -> Hay mo Fish Speech bang tool cua ban (D:\\Tool_voice) roi thu lai.")
            return False

        t0 = time.time()
        last = 0.0
        while time.time() - t0 < wait_sec:
            if stop_check and stop_check():
                return False
            if self.proc.poll() is not None:
                self.log("[LOI] Server Fish Speech thoat som. Mo bang tool cua ban de xem log.")
                return False
            if self._port_open():
                self.log("Server Fish Speech SAN SANG.")
                return True
            if time.time() - last > 10:
                last = time.time()
                self.log(f"  ... dang cho Fish Speech san sang ({int(time.time() - t0)}s)")
            time.sleep(1.5)
        self.log("[LOI] Fish Speech khong san sang sau khi cho.")
        return False

    # ---- sinh audio ----
    def generate(self, text, ref_audio=None, ref_text="", language=None, num_step=None):
        import ormsgpack
        references = []
        if ref_audio and os.path.exists(ref_audio):
            with open(ref_audio, "rb") as f:
                references = [{"audio": f.read(), "text": ref_text or ""}]
        payload = {
            "text": text,
            "references": references,
            "reference_id": None,
            "format": "wav",
            "max_new_tokens": 1024,
            "chunk_length": 200,
            "top_p": 0.7,
            "repetition_penalty": 1.2,
            "temperature": 0.7,
            "streaming": False,
            "use_memory_cache": "on",
            "seed": None,
        }
        data = ormsgpack.packb(payload)
        req = urllib.request.Request(
            self.url + "/v1/tts?format=msgpack", data=data,
            headers={"content-type": "application/msgpack"})
        with urllib.request.urlopen(req, timeout=600) as r:
            wav = r.read()
        import soundfile as sf
        a, sr = sf.read(io.BytesIO(wav), dtype="float32")
        if getattr(a, "ndim", 1) > 1:
            a = a.mean(axis=1)
        return np.ascontiguousarray(a, dtype=np.float32), sr

    # ---- tat ----
    def stop(self):
        if self.proc is None:
            return  # khong phai do ta bat -> giu nguyen
        if self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
