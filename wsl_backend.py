# -*- coding: utf-8 -*-
"""
Backend WSL cho GUI: quan ly server OmniVoice chay trong WSL (torch.compile)
va goi sinh audio qua HTTP.

- start(): neu server da chay (health OK) -> dung lai; chua thi tu khoi dong
  bang wsl/omni_run_server.sh roi CHO toi khi /health bao ready (poll).
- generate(): POST /generate -> tra ve (mono float32 numpy, sample_rate).
- stop(): tat server trong WSL (pkill) + terminate tien trinh wsl.exe.

Dung urllib (stdlib) nen KHONG can them thu vien ben Windows.
"""
from __future__ import annotations

import base64
import io
import json
import os
import socket
import subprocess
import time
import urllib.request

import numpy as np

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def win_to_wsl(path):
    """C:\\a\\b -> /mnt/c/a/b"""
    p = os.path.abspath(path)
    drive, rest = os.path.splitdrive(p)
    drive = drive.rstrip(":").lower()
    rest = rest.replace("\\", "/")
    return "/mnt/" + drive + rest


class WslServer:
    def __init__(self, port=8090, model_id=None, distro=None, log=print):
        self.port = port
        self.model_id = model_id        # model can chay (None = bat ky model nao dang co)
        self.distro = distro            # None = distro mac dinh cua WSL
        self.log = log
        self.proc = None
        self.url = f"http://127.0.0.1:{port}"
        here = os.path.dirname(os.path.abspath(__file__))
        self.script_wsl = win_to_wsl(os.path.join(here, "wsl", "omni_run_server.sh"))

    # ---- kiem tra trang thai ----
    def health(self, timeout=2.0):
        try:
            with urllib.request.urlopen(self.url + "/health", timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            return None

    def _wsl_prefix(self):
        cmd = ["wsl.exe"]
        if self.distro:
            cmd += ["-d", self.distro]
        return cmd + ["-u", "root", "--"]

    def _kill_any(self):
        """Tat BAT KY server omni_server.py nao trong WSL (de doi model / giai phong VRAM)."""
        try:
            subprocess.run(self._wsl_prefix() + ["pkill", "-f", "omni_server.py"],
                           creationflags=CREATE_NO_WINDOW, timeout=15)
            time.sleep(2)
        except Exception:
            pass

    # ---- khoi dong server ----
    def start(self, stop_check=None, wait_sec=900):
        h = self.health()
        if h and h.get("ready"):
            # da chay - kiem tra DUNG model can khong (VRAM chi du 1 model)
            if self.model_id is None or h.get("model") == self.model_id:
                self.log(f"Server WSL da chay san ({self.url} / {h.get('model')} / {h.get('device')}).")
                return True
            self.log(f"Server dang chay model '{h.get('model')}', can '{self.model_id}' "
                     f"-> khoi dong lai de doi model...")
            self._kill_any()

        cmd = self._wsl_prefix() + ["bash", self.script_wsl, str(self.port)]
        if self.model_id:
            cmd += [self.model_id]
        self.log(f"Dang khoi dong server OmniVoice trong WSL ({self.model_id or 'mac dinh'}) ...")
        self.log("  (Lan dau NAP MODEL + WARMUP torch.compile ~1-2 phut; doi model GOC se tai them ~vai GB)")
        try:
            self.proc = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            self.log(f"[LOI] Khong khoi dong duoc WSL: {e}")
            return False

        t0 = time.time()
        last_note = 0.0
        while time.time() - t0 < wait_sec:
            if stop_check and stop_check():
                self.log("Da huy cho server WSL.")
                return False
            if self.proc.poll() is not None:
                self.log("[LOI] Tien trinh WSL thoat som. Thu chay run_wsl_server.bat de xem log loi.")
                return False
            h = self.health()
            if h and h.get("ready"):
                self.log(f"Server WSL SAN SANG ({h.get('device')}).")
                return True
            # nhac tien trinh moi ~10s
            if time.time() - last_note > 10:
                last_note = time.time()
                self.log(f"  ... dang cho server WSL san sang ({int(time.time() - t0)}s)")
            time.sleep(1.5)

        self.log("[LOI] Server WSL khong san sang sau khi cho qua lau.")
        return False

    # ---- sinh audio ----
    def generate(self, text, ref_audio=None, ref_text="", language="vietnamese",
                 num_step=None, speed=None):
        payload = {"text": text, "language": language}
        if num_step:
            payload["num_step"] = int(num_step)
        if speed is not None:
            payload["speed"] = float(speed)
        if ref_audio and os.path.exists(ref_audio):
            with open(ref_audio, "rb") as f:
                payload["ref_audio_b64"] = base64.b64encode(f.read()).decode("ascii")
            if ref_text:
                payload["ref_text"] = ref_text
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url + "/generate", data=body,
                                     headers={"content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            wav = r.read()
        import soundfile as sf
        a, sr = sf.read(io.BytesIO(wav), dtype="float32")
        if getattr(a, "ndim", 1) > 1:
            a = a.mean(axis=1)
        return np.ascontiguousarray(a, dtype=np.float32), sr

    # ---- tat server ----
    def stop(self):
        # chi tat neu CHINH ta da khoi dong (proc != None). Server do nguoi dung
        # tu chay (run_wsl_server.bat) -> giu nguyen, khong dung.
        if self.proc is None:
            return
        try:
            subprocess.run(self._wsl_prefix() + ["pkill", "-f", "omni_server.py"],
                           creationflags=CREATE_NO_WINDOW, timeout=15)
        except Exception:
            pass
        if self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
