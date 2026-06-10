# -*- coding: utf-8 -*-
"""Tai san model OmniVoice ve cache HuggingFace de may khac dung duoc NGAY.
Dung snapshot_download + hf_transfer (tai nhanh, nhieu luong, on dinh hon) de
tranh treo/cham khi tai an danh tu HF Hub."""
import os
import sys

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Bat hf_transfer (tai nhanh) neu da cai
try:
    import hf_transfer  # noqa: F401
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
    print("hf_transfer: BAT (tai nhanh, nhieu luong)")
except Exception:
    print("hf_transfer: chua co -> tai cham hon (se duoc cai qua requirements)")

MODELS = [
    "splendor1811/omnivoice-vietnamese",   # tieng Viet 1000h
    "k2-fsa/OmniVoice",                     # ban GOC da ngon ngu
]


def main():
    try:
        from huggingface_hub import snapshot_download
    except Exception as e:
        print("Thieu huggingface_hub (se tai khi tao voice lan dau):", e)
        return 0
    for mid in MODELS:
        print(f"  Tai model: {mid} ...", flush=True)
        try:
            snapshot_download(repo_id=mid, max_workers=8)
            print(f"    OK: {mid}", flush=True)
        except Exception as e:
            print(f"    [Canh bao] khong tai duoc {mid}: {e}", flush=True)
            print("    -> Se tu tai khi tao voice lan dau (can mang).", flush=True)
    print("Xong tai model.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
