# Tool Voice - OmniVoice tiếng Việt 1000h (Local)

Giao diện & chức năng **giống tool tiếng Tây Ban Nha** (Fish Speech), nhưng dùng
**model fine-tune tiếng Việt 1000h** `splendor1811/omnivoice-vietnamese`, chạy
**local**, **nạp model 1 lần vào VRAM** rồi dùng lại cho tất cả text.

## Yêu cầu
- Windows + **Python 3.10 hoặc 3.11** (cài từ python.org, nhớ tích *Add Python to PATH*).
- Khuyến nghị **GPU NVIDIA ≥ 6–8GB VRAM**. Không có GPU vẫn chạy được trên CPU nhưng **chậm**.
- Internet cho **lần đầu** (tải thư viện + tải model ~vài GB). Sau đó chạy offline.

## Cài đặt (chỉ 1 lần)
1. Bấm đúp **`cai_dat.bat`** → đợi nó tạo `.venv` và cài PyTorch + OmniVoice.
   - Nếu máy không có GPU NVIDIA, nó tự lùi về bản CPU.
2. Xong.

## Chạy
1. Bấm đúp **`Tool_Voice_VN.bat`**.
2. Lần đầu app sẽ **tự nạp model vào VRAM** (log ở dưới hiện "Model SAN SANG").
   - Lần đầu tiên còn **tải model về** (~vài GB) → chờ một chút; các lần sau nhanh.
3. **Import File (\*.txt, \*.srt)** → mỗi dòng/mỗi phụ đề thành 1 hàng trong bảng.
4. (Tùy chọn) **Chọn Giọng Mẫu** = file WAV/MP3 5–15s để **clone giọng**.
   - Nếu để file `tên.txt` cùng tên cạnh file mẫu, nó tự đọc làm transcript (clone chuẩn hơn).
5. Chỉnh **Speed / Pitch / Số lượng AI** nếu muốn.
6. Bấm **Start** (1 file) hoặc **Chạy hàng loạt** (cả thư mục).
7. Kết quả: mỗi dòng ra 1 file `1.wav, 2.wav, ...` trong thư mục `<tên file>_tts`.

## Cách hoạt động (đúng yêu cầu "nạp VRAM 1 lần")
- `tts_engine.py` giữ **một** đối tượng model (singleton). Lần `generate()` đầu tiên
  nạp model vào VRAM; **mọi dòng sau dùng lại** model đó — không nạp lại.
- GPU chạy tuần tự nên `generate()` được khóa (lock) → "Số lượng AI" nhiều luồng
  vẫn an toàn (xếp hàng lần lượt trên GPU).

## Test nhanh engine không cần GUI
```bat
.venv\Scripts\activate.bat
python tts_engine.py "Xin chào, đây là bản thử nghiệm giọng nói tiếng Việt."
```
→ tạo file `_test_engine.wav`.

## Mẹo chất lượng (đặc biệt cho phụ đề ngắn / phim Trung dịch)
- Trước khi đưa vào: **gộp các dòng SRT vụn thành câu trọn** + **chuẩn hóa text**
  (chữ thường, số → chữ, bỏ ký tự lạ). Tool đã tự **thêm dấu câu cuối dòng** để
  tránh nuốt từ cuối, nhưng câu trọn vẹn vẫn cho ngữ điệu tốt hơn.
- Câu cực ngắn (1–2 từ) là chỗ mọi model "đoán độ dài" dễ lỗi nhất — nếu cần
  tuyệt đối không nuốt, cân nhắc thêm Piper cho riêng các dòng đó.

## Tinh chỉnh (tùy chọn)
Mở `tts_engine.py`:
- `NUM_STEP = 32` → đổi `16` để **chạy nhanh hơn** (chất lượng giảm nhẹ).
- `MODEL_ID` → đổi sang model OmniVoice khác nếu muốn.

## Lỗi thường gặp
- **`No module named 'omnivoice'`** → chưa cài: chạy lại `cai_dat.bat`.
- **CUDA out of memory** → giảm `NUM_STEP`, đặt "Số lượng AI" = 1, đóng app khác
  đang chiếm VRAM; hoặc dùng máy/GPU lớn hơn.
- **Tải model chậm/lỗi** → kiểm tra mạng; chạy lại, nó tải tiếp.
