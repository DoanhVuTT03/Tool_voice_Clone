#!/usr/bin/env bash
# Chay server OmniVoice trong WSL voi torch.compile (nhanh).
# Chay:  bash omni_run_server.sh [PORT]   (mac dinh PORT=8090)
set -e

# Tu suy ra duong dan project tu vi tri script -> chay duoc o BAT KY dau (portable)
SELF="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$SELF")"
VENV="$HOME/omni_tts_venv"
PORT="${1:-8090}"
MODEL_ID="${2:-}"                 # tham so 2 (tuy chon): id model HuggingFace
if [ -n "$MODEL_ID" ]; then
    export OMNI_MODEL_ID="$MODEL_ID"
    echo "Dung model: $MODEL_ID"
fi

if [ ! -f "$VENV/bin/activate" ]; then
    echo "[LOI] Chua co venv tai $VENV. Hay chay omni_bootstrap.sh truoc."
    exit 1
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"

# torch.compile: 1 = bat (che do an toan, KHONG dung reduce-overhead).
#   Neu van bi doc tung tu / mat tu -> dat OMNI_COMPILE=0 de TAT compile (chuan
#   nhu ban Windows, chi cham hon mot chut).
export OMNI_COMPILE=1
# Khong dat OMNI_COMPILE_MODE => dung inductor 'default' (an toan cho cau ngan).
cd "$PROJ"

echo "=================================================================="
echo " OmniVoice server (WSL, torch.compile) -> http://0.0.0.0:$PORT"
echo " Lan dau se NAP MODEL + WARMUP bien dich (~1-2 phut). Giu cua so nay mo."
echo " Khi thay dong 'SERVER READY' la dung duoc."
echo "=================================================================="
python3 omni_server.py --host 0.0.0.0 --port "$PORT"
