# Hướng dẫn cài Tool Voice Clone trên máy khác

Dành cho người dùng máy mới. Tool tự lo gần hết — bạn chỉ cần làm theo các bước.

## Bước 1 — Chạy file cài đặt
1. Mở **`ToolVoiceClone_Setup.exe`**.
2. Nếu hiện **"Windows protected your PC" (SmartScreen)** → bấm **"More info"** → **"Run anyway"**.
   (File chưa mua chứng chỉ ký số nên Windows cảnh báo — bình thường.)
3. Bấm Next → Install. Cài rất nhanh (chỉ chép mã nguồn ~2MB).

## Bước 2 — Mở app lần đầu (tự cài mọi thứ)
1. Mở **Tool Voice Clone** (Start Menu hoặc Desktop).
2. Lần đầu nó **tự động**:
   - Tải + cài **Python 3.11** nếu máy chưa có (im lặng, **không cần admin**).
   - Tạo môi trường + tải **PyTorch + OmniVoice**.
   - **Tải sẵn model** (tiếng Việt + bản đa ngôn ngữ) — **~vài GB**.
3. ⚠️ Cần **internet**, để cửa sổ chạy tới khi báo **"CAI DAT XONG"**. Chỉ làm **1 lần**.
4. Xong → app mở lên dùng được ngay (engine **OmniVoice Windows**).

## Bước 3 — (Khuyên dùng) Bật engine WSL để chạy NHANH ~2.6×
1. Vào thư mục cài app, chạy **`cai_dat_wsl.bat`**.
2. Nếu máy **chưa có WSL**:
   - Nó sẽ **xin quyền Admin** → hiện cửa sổ **UAC** → bấm **"Yes"**.
   - WSL cài xong → **KHỞI ĐỘNG LẠI máy**.
   - Mở lại `cai_dat_wsl.bat` để cài tiếp (tải model trong WSL ~vài GB).
3. Nếu UAC bị từ chối: mở **PowerShell (Run as administrator)** gõ `wsl --install`, reboot, rồi chạy lại.
4. Trong app, chọn engine **"OmniVoice VN (WSL nhanh)"** hoặc **"OmniVoice Base (WSL...)"**.

> Không bật WSL vẫn dùng được, chỉ chậm hơn (engine "Windows in-process").

## Khi nào cần Admin?
- **Chỉ khi cài WSL** (bước 3) — vì `wsl --install` là lệnh hệ thống.
- Cài app + Python + model **KHÔNG cần admin** (cài trong thư mục người dùng).

## Nếu Windows Security / Defender chặn hoặc làm chậm
Thêm **Exclusion (ngoại lệ)** cho các thư mục sau:
- `%LOCALAPPDATA%\Programs\ToolVoiceClone` (thư mục app)
- `%LOCALAPPDATA%\Programs\Python` (Python)

Cách thêm: **Windows Security** → *Virus & threat protection* → *Manage settings* → *Exclusions* → **Add an exclusion** → **Folder**.

(Thường không cần — chỉ làm nếu thấy bị chặn tải hoặc chạy rất chậm.)

## Yêu cầu máy
- Windows 10/11 64-bit.
- **GPU NVIDIA** (≥ 6–8GB VRAM) để nhanh; không có GPU vẫn chạy CPU (chậm).
- Ổ đĩa trống **~15–25GB** (model + thư viện; nếu dùng cả WSL thì model tải 2 nơi).
- Internet cho lần cài đầu.

## Lỗi thường gặp
- **Tải bị đứt giữa chừng** → chạy lại `cai_dat.bat` (trong thư mục app), nó tải tiếp.
- **App không mở** → mở `cai_dat.bat` xem dòng đỏ / mở `install_log.txt`.
- **Engine Fish Speech báo lỗi** → engine đó cần tool riêng `D:\Tool_voice` (không có trên máy mới). Cứ dùng các engine **OmniVoice** — đã đủ cho Việt + TBN/Pháp/Anh/Filipino.
