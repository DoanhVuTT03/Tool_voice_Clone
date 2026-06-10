# -*- coding: utf-8 -*-
"""
Server HTTP cho OmniVoice tieng Viet 1000h.

- Nap model 1 LAN vao VRAM khi server khoi dong (co the bat torch.compile qua
  bien moi truong OMNI_COMPILE=1 -> nhanh hon, nhat la tren Linux/WSL).
- Endpoint:
    GET  /health   -> trang thai san sang + thiet bi
    POST /generate -> sinh audio WAV cho 1 doan text (ho tro clone qua ref_audio_b64)

Chay:
    python omni_server.py --host 0.0.0.0 --port 8090
Dung chung tts_engine.py (cung thu muc) -> logic nap model giong het ban GUI.
"""
from __future__ import annotations

import argparse
import base64
import io
import os
import tempfile
from typing import Optional

from fastapi import FastAPI, Response
from pydantic import BaseModel
import soundfile as sf

import tts_engine as engine

app = FastAPI(title="OmniVoice Vietnamese TTS Server")


class GenReq(BaseModel):
    text: str
    language: str = "vietnamese"
    num_step: Optional[int] = None
    speed: Optional[float] = None            # chinh toc do NGAY trong model (khong nat giong)
    ref_audio_b64: Optional[str] = None      # base64 cua file giong mau (de clone)
    ref_text: str = ""


@app.on_event("startup")
def _startup():
    # nap model + warmup (kich hoat torch.compile neu bat)
    engine.warmup(progress=lambda m: print("[startup]", m, flush=True))
    print("[startup] SERVER READY", flush=True)


@app.get("/health")
def health():
    return {"ready": engine.is_loaded(), "device": engine.device_info(),
            "model": engine.MODEL_ID}


@app.post("/generate")
def generate(req: GenReq):
    ref_path = None
    try:
        if req.ref_audio_b64:
            data = base64.b64decode(req.ref_audio_b64)
            tf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tf.write(data)
            tf.close()
            ref_path = tf.name
        audio, sr = engine.generate(
            req.text, ref_audio=ref_path, ref_text=req.ref_text,
            language=req.language, num_step=req.num_step, speed_native=req.speed)
        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
        return Response(content=buf.getvalue(), media_type="audio/wav")
    finally:
        if ref_path and os.path.exists(ref_path):
            try:
                os.unlink(ref_path)
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8090)
    args = ap.parse_args()
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
