# Tool Voice Clone — Doanhbadboiz

Công cụ **clone giọng / text-to-speech chạy local**, lồng tiếng từ file `.srt`/`.txt`.
Tác giả: **Vũ Đức Doanh (Doanhbadboiz)**.

![logo](logo.png)

## Tính năng
- **Clone giọng** từ 1 file audio mẫu (WAV/MP3).
- Nhiều engine chọn trong **"Mô Hình AI"**:
  - **OmniVoice VN (WSL nhanh)** — tiếng Việt, tăng tốc bằng `torch.compile` trong WSL.
  - **OmniVoice VN (Windows in-process)** — tiếng Việt, không cần WSL (fallback).
  - **OmniVoice Base (WSL, đa ngôn ngữ)** — TBN / Pháp / Anh / Filipino (native speed).
  - **Fish Speech** — đa ngôn ngữ (server OpenAudio S1 riêng).
- Import **file** hoặc **cả thư mục** `.srt/.txt`; chạy hàng loạt.
- **Resume**: bỏ qua dòng đã tạo → dừng/crash chạy lại là đọc tiếp.
- Tạm dừng / Tiếp tục / Stop; chỉnh Speed / Pitch.

## Cài đặt (máy mới)
1. Cài **Python 3.10/3.11** (python.org, tích *Add to PATH*).
2. Chạy **`cai_dat.bat`** (tạo `.venv` + tải PyTorch + OmniVoice). Cần internet.
3. (Tùy chọn, để tăng tốc) cài **WSL2** + chạy **`cai_dat_wsl.bat`** một lần.
4. Mở app bằng shortcut **Tool Voice Clone** (hoặc `Tool_Voice_VN.bat`).

> Lần đầu tạo voice sẽ tải model về (~vài GB) — chỉ 1 lần.

## Hướng dẫn chi tiết
- `HUONG_DAN.md` — dùng cơ bản.
- `HUONG_DAN_WSL.md` — chạy WSL tăng tốc + đa engine + Resume.

## Ghi chú
- Engine **Fish Speech** dùng server riêng ở `D:\Tool_voice` (sửa `FISH_DIR` trong
  `fish_backend.py` nếu để chỗ khác). Các engine OmniVoice không cần Fish.
- Yêu cầu GPU NVIDIA để nhanh; không có GPU vẫn chạy CPU (chậm).
