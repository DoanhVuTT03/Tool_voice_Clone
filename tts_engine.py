# -*- coding: utf-8 -*-
"""
Engine TTS - OmniVoice tieng Viet 1000h (Local).

Nap model 1 LAN vao VRAM (singleton), dung lai cho TAT CA text.
- load_model(): tai/khoi tao model (lazy, thread-safe). Goi nhieu lan van chi nap 1 lan.
- generate(): sinh audio cho 1 doan text (co the clone giong tu ref_audio).
  Cac lan goi generate() deu tai SU DUNG cung 1 model da nap.

Vi 1 model tren 1 GPU chay tuan tu, generate() duoc bao ve bang 1 lock ->
nhieu luong (So luong AI) van an toan, chung se xep hang lan luot tren GPU.
"""
from __future__ import annotations

import io
import os
import sys
import threading
import numpy as np

# Sua loi 'charmap' codec khi nap model: thu vien (omnivoice/hf/tqdm) in ky tu
# Unicode ra stdout/stderr ma tren Windows mac dinh la cp1252 -> ep UTF-8.
for _nm in ("stdout", "stderr"):
    _st = getattr(sys, _nm, None)
    try:
        if _st is None:
            setattr(sys, _nm, open(os.devnull, "w", encoding="utf-8"))
        else:
            _st.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        try:
            setattr(sys, _nm, io.TextIOWrapper(_st.buffer, encoding="utf-8", errors="replace"))
        except Exception:
            pass

# Tai model nhanh + on dinh hon qua hf_transfer (neu da cai)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
try:
    import hf_transfer  # noqa: F401
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
except Exception:
    pass

# --------------------------------------------------------------------------- #
# Cau hinh
# --------------------------------------------------------------------------- #
# Model: mac dinh ban fine-tune tieng Viet 1000h; co the doi bang bien moi truong
# OMNI_MODEL_ID (vd 'k2-fsa/OmniVoice' cho ban GOC da ngon ngu).
MODEL_ID = os.environ.get("OMNI_MODEL_ID", "splendor1811/omnivoice-vietnamese")
SAMPLE_RATE = 24000                               # OmniVoice xuat 24 kHz
NUM_STEP = 32                                      # so buoc diffusion (16 = nhanh, 32 = net hon)

# Map ma ngon ngu (lay tu combobox) -> ten ngon ngu OmniVoice
LANG_MAP = {
    "vi": "vietnamese", "en": "english", "zh": "chinese", "ja": "japanese",
    "ko": "korean", "es": "spanish", "fr": "french", "de": "german",
    "it": "italian", "ru": "russian", "fil": "filipino",
}

# --------------------------------------------------------------------------- #
# Trang thai noi bo (singleton)
# --------------------------------------------------------------------------- #
_model = None
_load_lock = threading.Lock()    # bao ve buoc NAP model (chi nap 1 lan)
_gen_lock = threading.Lock()     # bao ve buoc SINH audio (GPU chay tuan tu)
_device = None
_dtype_name = None


def _pick_device():
    """Tu dong chon thiet bi: NVIDIA -> Apple MPS -> Intel XPU -> CPU."""
    import torch
    if torch.cuda.is_available():
        return "cuda:0", torch.float16
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps", torch.float16
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu", torch.float16
    return "cpu", torch.float32


def device_info() -> str:
    """Tra ve mo ta thiet bi dang dung (sau khi da nap model)."""
    if _device is None:
        return "(chua nap model)"
    return f"{_device} / {_dtype_name}"


def is_loaded() -> bool:
    return _model is not None


def load_model(progress=None):
    """Nap model 1 lan vao VRAM. An toan khi goi tu nhieu luong.
    progress: callable(str) de bao tien trinh ra GUI (tuy chon)."""
    global _model, _device, _dtype_name
    if _model is not None:
        return _model
    with _load_lock:
        if _model is not None:
            return _model
        import torch
        from omnivoice import OmniVoice

        _device, dtype = _pick_device()
        _dtype_name = str(dtype).replace("torch.", "")
        if progress:
            progress(f"Dang nap model OmniVoice tieng Viet (1000h) tren {_device} "
                     f"- lan dau se TAI MODEL ve ~vai GB, cac lan sau nhanh...")
        _model = OmniVoice.from_pretrained(MODEL_ID, device_map=_device, dtype=dtype)

        # torch.compile -> tang toc dang ke (nhat la tren Linux/WSL).
        # Bat bang bien moi truong OMNI_COMPILE=1 (server WSL se tu bat).
        if (os.environ.get("OMNI_COMPILE", "0").lower() in ("1", "true", "yes", "on")
                and str(_device).startswith("cuda")):
            try:
                # QUAN TRONG: KHONG dung mode='reduce-overhead' (CUDA graphs) -> voi cau
                # ngan/do dai THAY DOI no phat lai do thi cu => doc tung tu, mat tu, luc
                # loi luc khong. Mac dinh dung inductor 'default' (an toan, van nhanh hon
                # eager). Muon thu mode khac: dat bien OMNI_COMPILE_MODE=reduce-overhead...
                ckw = {"dynamic": True}
                cmode = os.environ.get("OMNI_COMPILE_MODE", "").strip()
                if cmode:
                    ckw["mode"] = cmode
                if progress:
                    progress(f"Bat torch.compile cho LLM (mode={cmode or 'default an toan'}; "
                             f"lan dau bien dich lau hon)...")
                _model.llm = torch.compile(_model.llm, **ckw)
            except Exception as e:
                if progress:
                    progress(f"Bo qua torch.compile ({e}).")

        if progress:
            progress(f"Model SAN SANG tren {device_info()}. Co the bam Start.")
        return _model


def warmup(progress=None, iters=2):
    """Nap model + chay thu vai nhip de KICH HOAT torch.compile (lan dau bien dich)
    -> cac lan sinh sau nhanh & on dinh. iters>=2 vi compile can vai luot."""
    import time as _t
    load_model(progress=progress)
    for i in range(max(1, iters)):
        try:
            t0 = _t.time()
            with _gen_lock:
                _model.generate(text="Xin chào, đây là bước khởi động engine.",
                                language="vietnamese", num_step=NUM_STEP)
            if progress:
                progress(f"Warmup {i + 1}/{iters}: {_t.time() - t0:.1f}s")
        except Exception as e:
            if progress:
                progress(f"Warmup loi (bo qua): {e}")
            break


def _to_mono_f32(audio):
    """Chuyen output (numpy hoac torch tensor, mono/stereo) -> mono float32 numpy."""
    try:
        import torch
        if isinstance(audio, torch.Tensor):
            audio = audio.detach().to("cpu").float().numpy()
    except Exception:
        pass
    audio = np.asarray(audio, dtype=np.float32)
    audio = np.squeeze(audio)
    if audio.ndim > 1:
        # gom ve mono theo truc co it phan tu hon (kenh)
        ch_axis = int(np.argmin(audio.shape))
        audio = audio.mean(axis=ch_axis)
    return np.ascontiguousarray(audio, dtype=np.float32)


def generate(text, ref_audio=None, ref_text="", language="vietnamese",
             num_step=None, speed_native=None):
    """Sinh audio cho 1 doan text. Tra ve (mono float32 numpy, sample_rate).

    text        : noi dung can doc.
    ref_audio   : duong dan file giong mau (WAV/MP3) de CLONE; None = giong mac dinh.
    ref_text    : ban ghi loi noi cua file mau (giup clone chuan hon, tuy chon).
    language    : ten ngon ngu OmniVoice (vd 'vietnamese').
    speed_native: neu dat, dung tham so speed cua OmniVoice (mac dinh None ->
                  de GUI tu chinh toc do bang librosa cho dong nhat voi tool goc).
    """
    model = load_model()
    kwargs = dict(text=text, language=language, num_step=int(num_step or NUM_STEP))
    if ref_audio:
        kwargs["ref_audio"] = ref_audio
        if ref_text:
            kwargs["ref_text"] = ref_text
    if speed_native is not None:
        kwargs["speed"] = float(speed_native)

    with _gen_lock:                      # GPU chay tuan tu -> serialize
        out = model.generate(**kwargs)

    audio = out[0] if isinstance(out, (list, tuple)) else out
    return _to_mono_f32(audio), SAMPLE_RATE


# --------------------------------------------------------------------------- #
# Chay thu nhanh tu dong lenh (kiem tra engine khong can GUI):
#   python tts_engine.py "Xin chao the gioi"
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys
    import soundfile as sf

    txt = sys.argv[1] if len(sys.argv) > 1 else "Xin chao, day la ban thu nghiem giong noi tieng Viet."
    print("Thiet bi se dung:", _pick_device())
    load_model(progress=print)
    a, sr = generate(txt)
    sf.write("_test_engine.wav", a, sr)
    print(f"Da xuat _test_engine.wav ({len(a)/sr:.2f}s @ {sr} Hz)")
