# Bước (1): Chạy OmniVoice trên WSL (torch.compile) + đo tốc độ

Mục tiêu: bọc OmniVoice thành **server chạy trong WSL/Linux với `torch.compile`** (giống
cách tool Tây Ban Nha tăng tốc) rồi **so tốc độ** với bản Windows in-process hiện tại.
Chưa đụng gì tới tool GUI đang chạy ngon — đây là phần thử nghiệm riêng.

## File liên quan
- `omni_server.py` — server HTTP, nạp model 1 lần, có `/generate` + `/health`.
- `wsl/omni_bootstrap.sh` — cài môi trường OmniVoice trong WSL (1 lần).
- `wsl/omni_run_server.sh` — chạy server trong WSL với `torch.compile`.
- `cai_dat_wsl.bat`, `run_wsl_server.bat` — launcher tiện cho Windows.
- `benchmark.py` — đo tốc độ (in-process vs server).
- `tts_engine.py` — đã thêm cờ `OMNI_COMPILE=1` để bật compile.

## Yêu cầu
- Đã có **WSL2** + distro Linux (Ubuntu). Nếu chưa: mở **PowerShell Admin** chạy
  `wsl --install` → khởi động lại máy. (Bạn đang chạy tool TBN trên WSL nên chắc đã có.)
- **Driver NVIDIA trên Windows** (đã có sẵn vì Fish Speech chạy được). Không cần cài
  CUDA toolkit riêng — bản torch cu128 tự kèm CUDA, GPU dùng qua driver Windows.

## Các bước

### 1) Cài môi trường WSL (1 lần)
Bấm đúp **`cai_dat_wsl.bat`** (hoặc mở WSL chạy tay):
```bash
wsl -u root
bash /mnt/d/Download/Tool_Voice_VN/wsl/omni_bootstrap.sh
```
Chờ tới khi thấy `TOOLVOICE_OMNI_BOOTSTRAP_DONE`. Nó cũng in `CUDA available: True` nếu
GPU dùng được trong WSL.

### 2) Chạy server WSL
Bấm đúp **`run_wsl_server.bat`** (giữ cửa sổ mở). Lần đầu nạp model + **warmup biên
dịch ~1–2 phút**; xong sẽ thấy dòng `SERVER READY`. Server lắng nghe `http://127.0.0.1:8090`.
> WSL2 tự forward localhost nên Windows gọi `127.0.0.1:8090` là tới.

### 3) Đo tốc độ — so 2 bản
Mở **PowerShell trong thư mục** project:

**a) Bản Windows in-process** (bản hiện tại):
```powershell
.\.venv\Scripts\python.exe benchmark.py
```

**b) Bản server WSL (torch.compile):**
```powershell
.\.venv\Scripts\python.exe benchmark.py --url http://127.0.0.1:8090
```

So sánh dòng **RTF trung bình** và **TB mỗi câu** của 2 lần. RTF càng nhỏ càng nhanh.

## Cách đọc kết quả
- `RTF 0.30` nghĩa là tạo 10s audio mất ~3s.
- Nếu bản WSL có **RTF/TB-mỗi-câu nhỏ hơn rõ** → WSL đáng để chuyển sang.
- Nếu **chênh ít** → giữ bản Windows in-process cho đơn giản.
- Câu warmup không tính giờ (đã loại phần compile lần đầu).

## Lưu ý / khắc phục
- **`CUDA available: False` trong WSL** → cập nhật driver NVIDIA Windows (bản hỗ trợ WSL),
  kiểm tra `nvidia-smi` chạy được trong WSL.
- **Warmup rất lâu / lỗi compile** → mở `wsl/omni_run_server.sh`, bỏ dòng
  `export OMNI_COMPILE=1` để chạy không compile (vẫn test được tốc độ Linux thuần).
- **VRAM**: đừng chạy đồng thời server WSL này + tool GUI Windows (2 model = gấp đôi VRAM).
- **Đổi `num_step`**: trong `tts_engine.py` đổi `NUM_STEP` (16 nhanh hơn, 32 nét hơn) rồi
  chạy lại benchmark để cân tốc độ/chất lượng.

---

# Bước (2): Dùng GUI với 2 engine (WSL nhanh ⇄ Windows in-process)

Đã tích hợp xong: GUI [tts_gui.py](tts_gui.py) giờ có ô **"Mô Hình AI"** chọn engine.
File mới: [wsl_backend.py](wsl_backend.py) (quản lý server WSL + gọi HTTP).

## Dùng thế nào
1. Mở tool như thường: **`Tool_Voice_VN.bat`**.
2. Ở ô **"Mô Hình AI"** chọn:
   - **`OmniVoice (WSL nhanh)`** ← mặc định, nhanh ~2.6×. Khi bấm **Start**, GUI **tự khởi
     động server WSL** (lần đầu warmup ~1–2 phút, log hiện "Server WSL SAN SANG"), rồi chạy.
   - **`OmniVoice (Windows in-process)`** ← bản cũ, đơn giản, không cần WSL (fallback).
3. Mọi thứ khác (Import File/Folder, Speed/Pitch, clone giọng, Start/Stop) **giữ nguyên**.

## Mẹo / lưu ý
- Muốn **xem log chi tiết server** (lần đầu compile): chạy **`run_wsl_server.bat`** TRƯỚC,
  đợi `SERVER READY`, rồi mở GUI và bấm Start — GUI thấy server đã chạy sẽ dùng lại ngay.
- **VRAM:** khi đóng GUI, nếu server do GUI tự bật thì nó **tự tắt** để giải phóng VRAM.
  Server bạn tự bật bằng `run_wsl_server.bat` thì GUI **không đụng tới** (giữ ấm để dùng lại).
- Đừng để **2 engine cùng nạp** (chạy in-process rồi lại bật WSL) khi VRAM nhỏ.
- Clone giọng ở chế độ WSL: GUI tự đọc file mẫu trên Windows và gửi sang server (base64),
  bạn không phải copy file vào WSL.

## Bước (3): đã ghép Fish Speech + thêm OmniVoice Base + Resume

Ô **"Mô Hình AI"** giờ có 4 engine:
| Engine | Model | Dùng cho |
|---|---|---|
| OmniVoice VN (WSL nhanh) | `splendor1811/omnivoice-vietnamese` | Tiếng Việt (chuẩn nhất) |
| OmniVoice VN (Windows in-process) | (như trên) | Tiếng Việt, fallback không cần WSL |
| **OmniVoice Base (WSL, đa ngôn ngữ)** | `k2-fsa/OmniVoice` | **TBN / Pháp / Anh / Filipino** |
| Fish Speech (đa ngôn ngữ) | OpenAudio S1 (D:\Tool_voice) | Dự phòng đa ngôn ngữ |

### OmniVoice Base — dùng cho tiếng khác
- Chọn engine **"OmniVoice Base (WSL...)"** + chọn **Ngôn Ngữ** đúng (es/fr/en/fil) → Start.
- **Chỉnh Speed dùng native** của model (không kéo-giãn) → **không nát giọng** như Fish Speech.
- ⚠️ **VRAM 12GB chỉ đủ 1 model OmniVoice**: khi đổi giữa VN ⇄ Base, GUI **tự tắt server cũ + nạp model mới** (đổi mất ~1-2 phút + lần đầu Base tải ~vài GB). Đừng chạy đồng thời.
- ⚠️ **Filipino chỉ có ~7.7 giờ dữ liệu** trong OmniVoice (TBN ~27.000h) → **chất lượng có thể rất kém**. Hãy test 1 đoạn ngắn trước; TBN/Pháp/Anh thì rất tốt.

### Resume (lưu tiến trình) — cho MỌI engine
- Ô tick **"Resume (bỏ qua dòng đã tạo)"** (mặc định bật).
- Khi bật: dòng nào đã có file `.wav` đầy đủ → **bỏ qua**. Dừng/crash/tắt máy rồi chạy lại
  là **đọc tiếp**, không làm lại từ đầu.
- Ghi file kiểu `.part` rồi đổi tên → crash giữa chừng **không để lại file hỏng**.
- Muốn tạo lại từ đầu → **bỏ tick** Resume (sẽ ghi đè).
