# -*- coding: utf-8 -*-
"""Tai san model OmniVoice ve cache HuggingFace de may khac dung duoc NGAY,
khong phai cho tai lan dau khi tao voice. Dung snapshot_download (khong can GPU,
khong nap model -> nhanh & nhe)."""
import os
import sys

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODELS = [
    "splendor1811/omnivoice-vietnamese",   # tieng Viet 1000h
    "k2-fsa/OmniVoice",                     # ban GOC da ngon ngu (TBN/Phap/Anh/Filipino)
]


def main():
    try:
        from huggingface_hub import snapshot_download
    except Exception as e:
        print("Thieu huggingface_hub (se tai khi tao voice lan dau):", e)
        return 0
    ok = True
    for mid in MODELS:
        print(f"  Tai model: {mid} ...", flush=True)
        try:
            snapshot_download(repo_id=mid)
            print(f"    OK: {mid}")
        except Exception as e:
            ok = False
            print(f"    [Canh bao] khong tai duoc {mid}: {e}")
            print("    -> Se tu tai khi tao voice lan dau (can mang).")
    print("Xong tai model." if ok else "Tai model chua day du (khong sao, se tai sau).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
