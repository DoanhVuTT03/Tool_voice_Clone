#!/usr/bin/env bash
# Cai dat moi truong OmniVoice tieng Viet trong WSL/Linux (chi 1 lan).
# Chay (nen chay voi quyen root):  bash omni_bootstrap.sh
# An toan khi chay lai nhieu lan: pip se bo qua goi da co, tai tiep goi con thieu.
set -e

# Tu suy ra duong dan project tu vi tri script (portable)
SELF="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$SELF")"
VENV="$HOME/omni_tts_venv"

SUDO=""
if [ "$(id -u)" -ne 0 ]; then SUDO="sudo"; fi

# pip chong dut mang: thu lai nhieu lan + timeout dai
export PIP_DEFAULT_TIMEOUT=120
PIP_OPTS="--retries 10 --timeout 120 --prefer-binary"

echo "[1/4] Cai goi he thong (python venv, ffmpeg, libsndfile)..."
$SUDO apt-get update -y
$SUDO apt-get install -y python3 python3-venv python3-pip ffmpeg libsndfile1

echo "[2/4] Tao moi truong ao: $VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install $PIP_OPTS --upgrade pip

echo "[3/4] Cai PyTorch (CUDA 12.8 - chay GPU qua WSL)..."
pip install $PIP_OPTS torch==2.8.0+cu128 torchaudio==2.8.0+cu128 \
    --extra-index-url https://download.pytorch.org/whl/cu128

echo "[4/5] Cai OmniVoice + thu vien server (tung goi mot de de tai lai neu dut mang)..."
pip install $PIP_OPTS numpy
pip install $PIP_OPTS scikit-learn
pip install $PIP_OPTS soundfile librosa
pip install $PIP_OPTS fastapi "uvicorn[standard]"
pip install $PIP_OPTS huggingface_hub hf_transfer
pip install $PIP_OPTS omnivoice

echo ""
echo "Kiem tra GPU trong WSL:"
python3 -c "import torch; print('  CUDA available:', torch.cuda.is_available(), '|', (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no GPU'))" || true

echo "[5/5] Tai san model OmniVoice (VN + Base) trong WSL - ~vai GB, chi 1 lan..."
python3 - <<'PYEOF' || true
import os
try:
    import hf_transfer  # tai nhanh
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
except Exception:
    pass
from huggingface_hub import snapshot_download
for m in ["splendor1811/omnivoice-vietnamese", "k2-fsa/OmniVoice"]:
    print("  tai", m, flush=True)
    try:
        snapshot_download(repo_id=m, max_workers=8)
        print("   OK", m)
    except Exception as e:
        print("   skip (se tai khi tao voice):", e)
PYEOF

echo ""
echo "Project se chay tu: $PROJ"
echo "TOOLVOICE_OMNI_BOOTSTRAP_DONE"
