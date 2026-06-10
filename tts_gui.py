# -*- coding: utf-8 -*-
"""
Tool Voice - OmniVoice Tieng Viet 1000h (Local)

Giao dien + chuc nang GIONG tool tieng Tay Ban Nha (Fish Speech), nhung thay
engine sang ban fine-tune tieng Viet 1000h "splendor1811/omnivoice-vietnamese".

- Model nap 1 LAN vao VRAM (qua tts_engine) -> dung lai cho TAT CA text.
- Import File (*.txt, *.srt): moi dong / moi phu de thanh 1 hang.
- Import Folder + "Chay hang loat": chay lan luot moi file .txt/.srt trong thu muc.
- Start = chay file dang nap. Tam dung <-> Tiep tuc, Stop.
- Speed / Pitch / So luong AI (luong dispatch; GPU chay tuan tu, an toan).
- Clone giong tuy chon qua file WAV/MP3 mau ("Chon Giong Mau").
- Tu dong nap model o nen khi mo app (khong can cua so server rieng).
"""
import io
import os
import re
import time
import threading
import datetime as _dt
from pathlib import Path
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np

import tts_engine as engine
from wsl_backend import WslServer
from fish_backend import FishServer

WSL_PORT = 8090
VN_MODEL = "splendor1811/omnivoice-vietnamese"   # fine-tune tieng Viet 1000h
BASE_MODEL = "k2-fsa/OmniVoice"                   # ban GOC da ngon ngu (646 thu tieng)

# Lua chon engine (ten hien thi).
#  - OmniVoice VN (WSL): tieng Viet, nhanh ~2.6x.
#  - OmniVoice VN (Windows in-process): tieng Viet, don gian/fallback.
#  - OmniVoice Base (WSL, da ngon ngu): TBN/Phap/Anh/Filipino, native speed.
#  - Fish Speech: da ngon ngu - dung server cua D:\Tool_voice.
MODELS = [
    "OmniVoice VN (WSL nhanh)",
    "OmniVoice VN (Windows in-process)",
    "OmniVoice Base (WSL, da ngon ngu)",
    "Fish Speech (da ngon ngu)",
]

# Combobox ngon ngu (ma + ten). Mac dinh tieng Viet.
LANGUAGES = [
    "vi (Tieng Viet)", "es (Tay Ban Nha)", "fr (Phap)", "en (English)",
    "fil (Philippines)", "zh (Trung)", "ja (Nhat)", "ko (Han)",
    "de (Duc)", "it (Y)", "ru (Nga)",
]


# --------------------------------------------------------------------------- #
# Doc/ tach file (de o module de test khong can GUI)
# --------------------------------------------------------------------------- #
def parse_srt(text):
    """Tra ve list (timing_str, content) tu noi dung SRT."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    blocks = re.split(r"\n\s*\n", text.strip())
    rows = []
    ts_re = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip() != ""]
        if not lines:
            continue
        timing = ""
        content_lines = []
        for l in lines:
            m = ts_re.search(l)
            if m:
                timing = f"{m.group(1)} --> {m.group(2)}"
                continue
            if l.strip().isdigit() and not content_lines and timing == "":
                continue
            content_lines.append(l.strip())
        content = " ".join(content_lines).strip()
        if content:
            rows.append((timing, content))
    return rows


def parse_txt(text):
    """Moi dong khong rong thanh 1 hang."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("﻿")
    rows = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            rows.append(("", line))
    return rows


_END_PUNCT = ".!?…。！？”\"')]}"


def normalize_text(text):
    """Tranh model cat tu cuoi: dam bao dong ket thuc bang dau cau."""
    t = (text or "").strip()
    if not t:
        return t
    if t[-1] not in _END_PUNCT:
        t += "."
    return t


def parse_file(path):
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".srt":
        return parse_srt(raw)
    return parse_txt(raw)


def lang_code(combo_value):
    """'vi (Tieng Viet)' -> 'vietnamese' (ten OmniVoice)."""
    code = (combo_value or "vi").split()[0].strip().lower()
    return engine.LANG_MAP.get(code, "vietnamese")


_SENT_SPLIT = re.compile(r"(?<=[.!?…。！？])\s+")


def split_sentences(text):
    """Tach 1 dong thanh cac CAU theo dau . ! ? -> doc tung cau roi noi lai.
    Tranh model bo roi 1 cau trong dong nhieu cau (vd 'Can than! La Loi Tuoc!')."""
    t = normalize_text(text)
    parts = [p.strip() for p in _SENT_SPLIT.split(t) if p.strip()]
    return [normalize_text(p) for p in parts] or [t]


# --- Phat hien output hong (loi NGAU NHIEN cua diffusion) -------------------- #
RMS_SILENCE = 0.012      # duoi muc nay coi nhu gan im lang
MIN_SEC_PER_SYL = 0.13   # toi thieu giay/am tiet; thuc te ~0.18-0.25 -> 0.13 la nguong an toan
ABS_MIN_SEC = 0.18       # san tuyet doi cho cau cuc ngan
MAX_TRIES = 4            # so lan tao lai toi da moi cau


def _count_syllables(text):
    """Dem am tiet tieng Viet ~ so 'tu' co chu cai (bo token chi co dau cau)."""
    return sum(1 for t in text.split() if any(c.isalpha() for c in t))


def _audio_rms(a):
    if a is None or len(a) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(np.asarray(a, dtype=np.float64)))))


def gen_with_retry(raw_gen, text, log=None):
    """Tao 1 cau, TU PHAT HIEN hong (gan im / ngan bat thuong so voi so am tiet)
    roi TAO LAI toi MAX_TRIES lan. Giu lai ban DAI NHAT (gan day du nhat) neu deu hong."""
    syl = _count_syllables(text)
    min_ok = max(ABS_MIN_SEC, syl * MIN_SEC_PER_SYL)
    best = None
    best_dur = -1.0
    for i in range(MAX_TRIES):
        a, sr = raw_gen(text)
        a = np.asarray(a, dtype=np.float32)
        dur = len(a) / float(sr or 24000)
        rms = _audio_rms(a)
        if dur > best_dur:
            best, best_dur = (a, sr), dur
        if rms >= RMS_SILENCE and dur >= min_ok:        # dat -> dung luon
            return a, sr
        if log:
            log(f"  [tao lai {i + 1}/{MAX_TRIES}] '{text[:34]}' "
                f"dur={dur:.2f}s (can>={min_ok:.2f}) rms={rms:.3f}")
    return best if best else (np.zeros(1, dtype=np.float32), 24000)


# --- Cat "tieng gio"/nhieu o duoi + fade-out (bo tieng giat o cau ngan) -------- #
TAIL_TRIM_REL = 0.02     # nguong tuong doi (so voi dinh) de coi la "nhieu duoi"
TAIL_PAD_MS = 40         # giu lai 40ms quanh phan co tieng (tu nhien, khong cut got)
FADE_OUT_MS = 15         # fade cuoi de bo tieng giat/click


def _trim_tail(a, sr):
    """Cat phan nhieu/gio o DAU va CUOI (theo nang luong) + fade-out cuoi."""
    if a is None or len(a) == 0:
        return a
    peak = float(np.max(np.abs(a)))
    if peak <= 0:
        return a
    thr = max(peak * TAIL_TRIM_REL, 0.005)
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    pad = int(sr * TAIL_PAD_MS / 1000)
    start = max(0, idx[0] - pad)
    end = min(len(a), idx[-1] + pad)
    a = a[start:end].copy()
    f = int(sr * FADE_OUT_MS / 1000)
    if f > 0 and len(a) > f:
        a[-f:] = a[-f:] * np.linspace(1.0, 0.0, f, dtype=np.float32)
    return a


def gen_line(raw_gen, content, log=None):
    """GIONG BAN GOC: tao CA DONG trong 1 lan goi (khong tach cau, khong cat duoi,
    khong dung toi audio -> khong gay cut tu / khoang lang la).
    Luoi an toan DUY NHAT: neu output GAN NHU IM LANG hoan toan (vd chi co gio,
    kieu file 54) thi tao lai toi 3 lan. Cac truong hop khac giu nguyen y model."""
    text = normalize_text(content)
    best = None
    best_rms = -1.0
    for i in range(3):
        a, sr = raw_gen(text)
        a = np.asarray(a, dtype=np.float32)
        rms = _audio_rms(a)
        if rms > best_rms:
            best, best_rms = (a, sr), rms
        if rms >= 0.012:               # co tieng noi -> nhan luon (khong dung chinh)
            return a, sr
        if log:
            log(f"  [tao lai {i + 1}/3] '{text[:34]}' gan im lang -> thu lai")
    return best if best else (np.zeros(1, dtype=np.float32), 24000)


def apply_fx(audio, sr, speed, pitch):
    """Ap speed (giu cao do) / pitch (librosa) cho audio tho -> tra ve WAV bytes.
    Dung chung cho ca 2 backend (in-process & WSL)."""
    import soundfile as sf
    if abs(speed - 1.0) >= 1e-3 or int(pitch) != 0:
        import librosa
        if abs(speed - 1.0) >= 1e-3:
            audio = librosa.effects.time_stretch(audio, rate=float(speed))
        if int(pitch) != 0:
            audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=int(pitch))
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Dang nhap (Supabase) + hien han dung
# --------------------------------------------------------------------------- #
def _parse_ts(s):
    try:
        return _dt.datetime.fromisoformat((s or "").strip().replace("Z", "+00:00"))
    except Exception:
        return None


def _fmt_remaining(expires_at):
    """Tra ve (han_text, conlai_text)."""
    exp = _parse_ts(expires_at)
    if not exp:
        return "?", ""
    now = _dt.datetime.now(_dt.timezone.utc)
    han = exp.astimezone().strftime("%d/%m/%Y %H:%M")
    delta = exp - now
    if delta.total_seconds() <= 0:
        return han, "DA HET HAN"
    return han, f"con {delta.days} ngay {int(delta.seconds // 3600)} gio"


def login_gate(root):
    """Man dang nhap modal. Tra dict {username,token,expires_at} hoac None."""
    import voice_auth
    result = {}
    win = tk.Toplevel(root)
    win.title("Dang nhap - Tool Voice Clone")
    win.geometry("390x250")
    win.resizable(False, False)
    win.grab_set()
    try:
        win.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico"))
    except Exception:
        pass

    ttk.Label(win, text="TOOL VOICE CLONE", font=("", 14, "bold")).pack(pady=(16, 0))
    ttk.Label(win, text="Doanhbadboiz - dang nhap de su dung", foreground="#666").pack()

    frm = ttk.Frame(win); frm.pack(pady=10, padx=22, fill="x")
    ttk.Label(frm, text="Tai khoan:").grid(row=0, column=0, sticky="e", pady=5, padx=4)
    e_user = ttk.Entry(frm, width=26); e_user.grid(row=0, column=1, pady=5)
    ttk.Label(frm, text="Mat khau:").grid(row=1, column=0, sticky="e", pady=5, padx=4)
    e_pass = ttk.Entry(frm, width=26, show="*"); e_pass.grid(row=1, column=1, pady=5)
    var_rem = tk.BooleanVar(value=True)
    ttk.Checkbutton(frm, text="Ghi nho dang nhap", variable=var_rem).grid(row=2, column=1, sticky="w")

    lbl_msg = ttk.Label(win, text="", foreground="#c00", wraplength=350); lbl_msg.pack()

    rem = voice_auth.load_remember()
    if rem:
        e_user.insert(0, rem[0]); e_pass.insert(0, rem[1])

    def do_login():
        u = e_user.get().strip(); p = e_pass.get()
        if not u or not p:
            lbl_msg.config(text="Nhap tai khoan va mat khau."); return
        btn.config(state="disabled"); lbl_msg.config(text="Dang dang nhap...")
        win.update_idletasks()
        try:
            r = voice_auth.login(u, p)
        except voice_auth.AuthConfigError as e:
            lbl_msg.config(text=f"Loi cau hinh: {e}"); btn.config(state="normal"); return
        except voice_auth.AuthNetworkError as e:
            lbl_msg.config(text=f"Loi mang: {e}"); btn.config(state="normal"); return
        if not r.get("ok"):
            lbl_msg.config(text=r.get("reason", "Dang nhap that bai")); btn.config(state="normal"); return
        if var_rem.get():
            voice_auth.save_remember(u, p)
        else:
            voice_auth.clear_remember()
        result.update({"username": r.get("username", u), "token": r.get("token"),
                       "expires_at": r.get("expires_at")})
        win.destroy()

    btn = ttk.Button(win, text="Dang nhap", command=do_login); btn.pack(pady=10)
    e_pass.bind("<Return>", lambda e: do_login())
    win.protocol("WM_DELETE_WINDOW", win.destroy)
    root.wait_window(win)
    return result or None


# --------------------------------------------------------------------------- #
# GUI
# --------------------------------------------------------------------------- #
class App:
    def __init__(self, root, auth=None):
        self.auth = auth
        self.root = root
        root.title("Tool Voice - OmniVoice Tieng Viet 1000h (Local)")
        root.geometry("1180x800")

        # state
        self.rows = []
        self.input_path = None
        self.batch_files = []
        self.ref_audio_path = None
        self.ref_text = ""
        self.ref_name = ""

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()               # set => chay, clear => tam dung
        self.runner_thread = None
        self.running = False

        self.wsl = None                      # backend OmniVoice WSL (tao khi can)
        self.fish = None                     # backend Fish Speech (tao khi can)

        self.start_time = 0.0
        self.done_count = 0

        self._build_ui()
        if self.auth:
            self._start_heartbeat()
        self._start_update_watch()           # tu kiem tra ban moi moi 30 phut
        # chuan bi engine theo lua chon mac dinh (o nen)
        threading.Thread(target=self.prepare_default, daemon=True).start()
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -------------------- dung UI -------------------- #
    def _build_ui(self):
        if self.auth:
            self._build_auth_banner()
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=8, pady=6)

        # ----- Voice Generation -----
        vg = ttk.LabelFrame(top, text="Voice Generation")
        vg.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.btn_ref = ttk.Button(vg, text="Chon Giong Mau\n(File WAV/MP3 de clone)",
                                  command=self.choose_reference, width=24)
        self.btn_ref.grid(row=0, column=0, rowspan=2, padx=8, pady=8, sticky="ns")

        ttk.Label(vg, text="Ngon Ngu:").grid(row=0, column=1, sticky="e", padx=4, pady=6)
        self.cmb_lang = ttk.Combobox(vg, values=LANGUAGES, state="readonly", width=22)
        self.cmb_lang.set("vi (Tieng Viet)")
        self.cmb_lang.grid(row=0, column=2, sticky="w", padx=4, pady=6)
        self.lbl_ref = ttk.Label(vg, text="Chua chon file mau (WAV)", foreground="#888")
        self.lbl_ref.grid(row=0, column=3, sticky="w", padx=8)

        ttk.Label(vg, text="Mo Hinh AI:").grid(row=1, column=1, sticky="e", padx=4, pady=6)
        self.cmb_model = ttk.Combobox(vg, values=MODELS, state="readonly", width=24)
        self.cmb_model.current(0)            # mac dinh: WSL (nhanh)
        self.cmb_model.grid(row=1, column=2, sticky="w", padx=4, pady=6)
        ttk.Button(vg, text="Bo giong mau", command=self.clear_reference).grid(
            row=1, column=3, sticky="w", padx=8)

        # ----- Change voice settings -----
        cv = ttk.LabelFrame(top, text="Change voice settings")
        cv.pack(side="left", fill="y")

        ttk.Label(cv, text="Speed:").grid(row=0, column=0, sticky="e", padx=6, pady=8)
        self.var_speed = tk.DoubleVar(value=1.00)
        ttk.Spinbox(cv, from_=0.5, to=2.0, increment=0.05, textvariable=self.var_speed,
                    width=10, format="%.2f").grid(row=0, column=1, padx=6, pady=8)

        ttk.Label(cv, text="Pitch:").grid(row=1, column=0, sticky="e", padx=6, pady=8)
        self.var_pitch = tk.IntVar(value=0)
        ttk.Spinbox(cv, from_=-12, to=12, increment=1, textvariable=self.var_pitch,
                    width=10).grid(row=1, column=1, padx=6, pady=8)

        ttk.Label(cv, text="So luong AI:").grid(row=2, column=0, sticky="e", padx=6, pady=8)
        self.var_threads = tk.IntVar(value=1)
        ttk.Spinbox(cv, from_=1, to=8, increment=1, textvariable=self.var_threads,
                    width=10).grid(row=2, column=1, padx=6, pady=8)

        # Resume: bo qua dong da co .wav -> chay lai sau khi dung/crash la doc TIEP
        self.var_resume = tk.BooleanVar(value=True)
        ttk.Checkbutton(cv, text="Resume (bo qua dong da tao)",
                        variable=self.var_resume).grid(row=3, column=0, columnspan=2,
                                                        sticky="w", padx=6, pady=(0, 8))

        # ----- Batch Job Options -----
        bj = ttk.LabelFrame(self.root, text="Batch Job Options")
        bj.pack(fill="x", padx=8, pady=4)
        ttk.Label(bj, text="Thu muc:").pack(side="left", padx=6, pady=8)
        self.var_folder = tk.StringVar()
        ttk.Entry(bj, textvariable=self.var_folder).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(bj, text="...", width=4, command=self.choose_folder).pack(side="left", padx=2)
        self.btn_batch = ttk.Button(bj, text="Chay hang loat", command=self.start_batch)
        self.btn_batch.pack(side="left", padx=6)

        # ----- status line -----
        self.lbl_status = ttk.Label(
            self.root, text="Subtitles (Done: 0  Threads: 1  Total: 0)   Elapsed: 0s")
        self.lbl_status.pack(fill="x", padx=10, pady=(2, 0))

        # ----- control buttons -----
        ctl = ttk.Frame(self.root)
        ctl.pack(fill="x", padx=8, pady=4)
        self.btn_start = ttk.Button(ctl, text="Start", command=self.start_single)
        self.btn_start.pack(side="left", padx=3)
        self.btn_pause = ttk.Button(ctl, text="Tam dung", command=self.toggle_pause, state="disabled")
        self.btn_pause.pack(side="left", padx=3)
        self.btn_stop = ttk.Button(ctl, text="Stop", command=self.stop_run, state="disabled")
        self.btn_stop.pack(side="left", padx=3)
        ttk.Button(ctl, text="Import File (*.txt, *.srt)", command=self.import_file).pack(side="left", padx=10)
        ttk.Button(ctl, text="Import Folder", command=self.import_folder).pack(side="left", padx=3)

        # ----- table -----
        cols = ("id", "output", "timing", "content", "voice", "status")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", height=16)
        headers = {"id": ("Id", 40), "output": ("Output", 90), "timing": ("Timing", 150),
                   "content": ("Content", 520), "voice": ("Voice #", 70), "status": ("Status", 180)}
        for c in cols:
            t, w = headers[c]
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w")
        vsb = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="top", fill="both", expand=True, padx=8, pady=4)

        # ----- log -----
        self.txt_log = tk.Text(self.root, height=6, wrap="word")
        self.txt_log.pack(fill="x", padx=8, pady=(0, 8))
        self.log("San sang. Chon engine o 'Mo Hinh AI' (WSL = nhanh ~2.6x; in-process = don gian).")

    # -------------------- helpers (thread-safe GUI) -------------------- #
    def log(self, msg):
        def _do():
            self.txt_log.insert("end", msg + "\n")
            self.txt_log.see("end")
        self.root.after(0, _do)

    def set_row(self, iid, voice=None, status=None):
        def _do():
            if voice is not None:
                self.tree.set(iid, "voice", voice)
            if status is not None:
                self.tree.set(iid, "status", status)
        self.root.after(0, _do)

    def refresh_status(self):
        total = len(self.rows)
        el = int(time.time() - self.start_time) if self.running else 0
        txt = (f"Subtitles (Done: {self.done_count}  Threads: {self.var_threads.get()}  "
               f"Total: {total})   Elapsed: {el}s")
        self.root.after(0, lambda: self.lbl_status.config(text=txt))

    # -------------------- dang nhap / han dung -------------------- #
    def _build_auth_banner(self):
        BG = "#111827"          # slate dam (header)
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x")
        inner = tk.Frame(bar, bg=BG)
        inner.pack(fill="x", padx=14, pady=7)
        # trai: tai khoan
        self.lbl_acc = tk.Label(inner, text="", bg=BG, fg="#e5e7eb",
                                font=("Segoe UI", 10, "bold"))
        self.lbl_acc.pack(side="left")
        # phai: dem nguoc thoi gian (icon dong ho + so giay nhay)
        self.lbl_exp = tk.Label(inner, text="", bg=BG, fg="#34d399",
                                font=("Segoe UI Semibold", 10))
        self.lbl_exp.pack(side="right")
        self._refresh_expiry()

    def _refresh_expiry(self):
        if not self.auth or not hasattr(self, "lbl_exp"):
            return
        self.lbl_acc.config(text=f"\U0001F464  {self.auth.get('username', '')}")
        exp = _parse_ts(self.auth.get("expires_at"))
        if not exp:
            self.lbl_exp.config(text="")
        else:
            secs = int((exp - _dt.datetime.now(_dt.timezone.utc)).total_seconds())
            if secs <= 0:
                self.lbl_exp.config(text="⛔  Tai khoan da het han", fg="#f87171")
            else:
                d, r = divmod(secs, 86400)
                h, r = divmod(r, 3600)
                m, s = divmod(r, 60)
                han = exp.astimezone().strftime("%d/%m/%Y %H:%M")
                col = "#34d399" if d >= 7 else ("#fbbf24" if d >= 1 else "#f87171")
                self.lbl_exp.config(
                    text=f"⏳  Con {d} ngay  {h:02d}:{m:02d}:{s:02d}     •  Het han {han}",
                    fg=col)
        self.root.after(1000, self._refresh_expiry)     # nhay moi giay (real-time)

    def _start_heartbeat(self):
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        import voice_auth
        while True:
            time.sleep(60)
            try:
                r = voice_auth.validate(self.auth.get("username"), self.auth.get("token"))
            except Exception:
                continue  # loi mang tam thoi -> bo qua, khong da nguoi dung
            if not r.get("ok"):
                self.root.after(0, lambda rr=r: self._kick(rr.get("reason", "Phien het hieu luc")))
                return
            if r.get("expires_at"):
                self.auth["expires_at"] = r["expires_at"]

    def _kick(self, reason):
        try:
            messagebox.showwarning("Phien dang nhap", f"{reason}\n\nTool se dong.")
        except Exception:
            pass
        self.on_close()

    # -------------------- tu kiem tra cap nhat (dinh ky) -------------------- #
    def _start_update_watch(self):
        self._update_snooze_until = 0.0
        threading.Thread(target=self._update_watch_loop, daemon=True).start()

    def _update_watch_loop(self):
        import updater
        while True:
            time.sleep(1800)                 # 30 phut
            if time.time() < getattr(self, "_update_snooze_until", 0.0):
                continue
            try:
                info = updater.check_for_update()
            except Exception:
                info = None
            if info:
                self.root.after(0, lambda i=info: self._prompt_update(i))

    def _prompt_update(self, info):
        import updater
        # bam "De sau" -> tam an 4 gio (khong hoi lai lien tuc)
        self._update_snooze_until = time.time() + 4 * 3600
        if updater.prompt_and_download(self.root, info):
            self.on_close()

    # -------------------- giong mau -------------------- #
    def choose_reference(self):
        path = filedialog.askopenfilename(
            title="Chon file giong mau (WAV/MP3)",
            filetypes=[("Audio", "*.wav *.mp3 *.flac *.ogg"), ("All", "*.*")])
        if not path:
            return
        p = Path(path)
        self.ref_audio_path = str(p)
        self.ref_name = p.name
        # tim transcript di kem: cung ten .txt hoac .lab
        self.ref_text = ""
        for ext in (".txt", ".lab"):
            sc = p.with_suffix(ext)
            if sc.exists():
                self.ref_text = sc.read_text(encoding="utf-8", errors="replace").strip()
                break
        note = f"  (transcript: {len(self.ref_text)} ky tu)" if self.ref_text else "  (khong co transcript)"
        self.lbl_ref.config(text=p.name + note, foreground="#070")
        self.log(f"Da chon giong mau: {p.name}{note}")

    def clear_reference(self):
        self.ref_audio_path = None
        self.ref_text = ""
        self.ref_name = ""
        self.lbl_ref.config(text="Chua chon file mau (WAV)", foreground="#888")
        self.log("Da bo giong mau (dung giong mac dinh cua model).")

    # -------------------- import file/folder -------------------- #
    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self.rows = []
        for i, (timing, content) in enumerate(rows, start=1):
            iid = self.tree.insert("", "end", values=(i, f"{i}.wav", timing, content, "", "Waiting..."))
            self.rows.append({"iid": iid, "idx": i, "output": f"{i}.wav",
                              "timing": timing, "content": content})
        self.done_count = 0
        self.refresh_status()

    def import_file(self):
        path = filedialog.askopenfilename(
            title="Import File", filetypes=[("Text/SRT", "*.txt *.srt"), ("All", "*.*")])
        if not path:
            return
        try:
            rows = parse_file(path)
        except Exception as e:
            messagebox.showerror("Loi", f"Khong doc duoc file:\n{e}")
            return
        self.input_path = path
        self._populate_table(rows)
        kind = "SRT" if path.lower().endswith(".srt") else "TXT"
        self.log(f"Da nap {kind}: {Path(path).name}  ->  {len(rows)} dong.")

    def import_folder(self):
        folder = filedialog.askdirectory(title="Import Folder (chua .txt/.srt)")
        if not folder:
            return
        self.var_folder.set(folder)
        self._scan_folder(folder)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Chon thu muc")
        if folder:
            self.var_folder.set(folder)
            self._scan_folder(folder)

    def _scan_folder(self, folder):
        files = sorted([str(p) for p in Path(folder).iterdir()
                        if p.suffix.lower() in (".txt", ".srt")])
        self.batch_files = files
        self.log(f"Thu muc: {folder}  ->  {len(files)} file (.txt/.srt).")
        if files:
            try:
                self._populate_table(parse_file(files[0]))
                self.input_path = files[0]
            except Exception:
                pass

    # -------------------- backend (engine) -------------------- #
    def current_mode(self):
        """'omni_vn_wsl' / 'omni_vn_inproc' / 'omni_base_wsl' / 'fish'."""
        v = self.cmb_model.get().lower()
        if "fish" in v:
            return "fish"
        if "base" in v:
            return "omni_base_wsl"
        if "in-process" in v:
            return "omni_vn_inproc"
        return "omni_vn_wsl"

    def _wsl_model_for(self, mode):
        return BASE_MODEL if mode == "omni_base_wsl" else VN_MODEL

    def prepare_default(self):
        """Chuan bi nhe theo engine mac dinh (chay o nen khi mo app)."""
        mode = self.current_mode()
        if mode in ("omni_vn_wsl", "omni_base_wsl"):
            self.log("Engine: OmniVoice (WSL). Server se tu khoi dong khi bam Start.")
            self.log("  (Muon xem log chi tiet: chay san run_wsl_server.bat truoc.)")
            try:
                self.wsl = WslServer(port=WSL_PORT, model_id=self._wsl_model_for(mode), log=self.log)
                h = self.wsl.health()
                if h and h.get("ready"):
                    self.log(f"Server WSL da san sang ({h.get('model')} / {h.get('device')}).")
            except Exception:
                pass
        elif mode == "fish":
            self.log("Engine: Fish Speech (da ngon ngu). Server 8080 se tu bat khi bam Start.")
        else:
            self.log("Engine: OmniVoice VN (Windows in-process). Dang nap model o nen...")
            self.ensure_backend()

    def ensure_backend(self, stop_check=None):
        """Dam bao engine dang chon da san sang. Tra ve True khi OK."""
        mode = self.current_mode()
        if mode in ("omni_vn_wsl", "omni_base_wsl"):
            mid = self._wsl_model_for(mode)
            # VRAM chi du 1 model -> neu server dang giu model khac thi tao lai voi model dung
            if self.wsl is None or self.wsl.model_id != mid:
                if self.wsl is not None:
                    self.wsl.stop()
                self.wsl = WslServer(port=WSL_PORT, model_id=mid, log=self.log)
            return self.wsl.start(stop_check=stop_check)
        if mode == "fish":
            if self.fish is None:
                self.fish = FishServer(log=self.log)
            return self.fish.start(stop_check=stop_check)
        try:
            engine.load_model(progress=self.log)
            return True
        except Exception as e:
            self.log(f"[LOI] Khong nap duoc model in-process: {e}")
            self.log("    -> Kiem tra da cai 'omnivoice' + torch (xem HUONG_DAN.md).")
            return False

    # -------------------- dieu khien chay -------------------- #
    def _set_running_ui(self, running):
        self.running = running
        st_run = "disabled" if running else "normal"
        st_act = "normal" if running else "disabled"
        self.btn_start.config(state=st_run)
        self.btn_batch.config(state=st_run)
        self.btn_pause.config(state=st_act, text="Tam dung")
        self.btn_stop.config(state=st_act)

    def start_single(self):
        if self.running:
            return
        if not self.rows:
            messagebox.showinfo("Thong bao", "Chua co noi dung. Hay Import File truoc.")
            return
        self.runner_thread = threading.Thread(
            target=self._run_files, args=([self.input_path],), daemon=True)
        self._begin_run()

    def start_batch(self):
        if self.running:
            return
        if not self.batch_files:
            messagebox.showinfo("Thong bao", "Chua chon thu muc co file .txt/.srt.")
            return
        self.runner_thread = threading.Thread(
            target=self._run_files, args=(list(self.batch_files),), daemon=True)
        self._begin_run()

    def _begin_run(self):
        self.stop_event.clear()
        self.pause_event.set()
        self.done_count = 0
        self.start_time = time.time()
        self._set_running_ui(True)
        self._tick_elapsed()
        self.runner_thread.start()

    def _tick_elapsed(self):
        if self.running:
            self.refresh_status()
            self.root.after(1000, self._tick_elapsed)

    def toggle_pause(self):
        if not self.running:
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.btn_pause.config(text="Tiep tuc")
            self.log("== Tam dung ==")
        else:
            self.pause_event.set()
            self.btn_pause.config(text="Tam dung")
            self.log("== Tiep tuc ==")

    def stop_run(self):
        if not self.running:
            return
        self.stop_event.set()
        self.pause_event.set()
        self.log("== Stop: dang dung lai... ==")

    def _run_files(self, files):
        try:
            self.log(f"Dang chuan bi engine: {self.cmb_model.get()} ...")
            if not self.ensure_backend(stop_check=lambda: self.stop_event.is_set()):
                self.log("[LOI] Khong chay duoc vi engine chua san sang.")
                return
            for fpath in files:
                if self.stop_event.is_set():
                    break
                if fpath is None:
                    rows = self.rows
                else:
                    if len(files) > 1:
                        try:
                            parsed = parse_file(fpath)
                        except Exception as e:
                            self.log(f"[LOI] Bo qua {Path(fpath).name}: {e}")
                            continue
                        self.input_path = fpath
                        self.root.after(0, lambda r=parsed: self._populate_table(r))
                        time.sleep(0.2)
                    rows = self.rows
                self.log(f"--- Bat dau: {Path(fpath).name if fpath else 'file hien tai'} "
                         f"({len(rows)} dong) ---")
                self._generate(rows, fpath)
            self.log("=== HOAN TAT ===" if not self.stop_event.is_set() else "=== DA DUNG ===")
        finally:
            self.root.after(0, lambda: self._set_running_ui(False))
            self.refresh_status()

    def _generate(self, rows, fpath):
        if fpath:
            base = Path(fpath)
            outdir = base.parent / (base.stem + "_tts")
        else:
            outdir = Path(__file__).resolve().parent / "output_tts"
        outdir.mkdir(parents=True, exist_ok=True)
        self.log(f"Output -> {outdir}")

        n_workers = max(1, int(self.var_threads.get()))
        id_q = Queue()
        for i in range(1, n_workers + 1):
            id_q.put(i)

        speed = float(self.var_speed.get())
        pitch = int(self.var_pitch.get())
        language = lang_code(self.cmb_lang.get())
        ref_audio = self.ref_audio_path
        ref_text = self.ref_text
        mode = self.current_mode()
        is_omni = mode.startswith("omni")
        # OmniVoice: chinh toc do NATIVE trong model (khong nat giong).
        # Fish Speech: khong co native speed -> chinh bang librosa (fx) o duoi.
        native_speed = speed if is_omni else None
        fx_speed = 1.0 if is_omni else speed

        def raw_gen(text):
            """Sinh audio tho (mono float32, sr) tu engine dang chon."""
            if mode in ("omni_vn_wsl", "omni_base_wsl"):
                return self.wsl.generate(text, ref_audio=ref_audio, ref_text=ref_text,
                                         language=language, speed=native_speed)
            if mode == "fish":
                return self.fish.generate(text, ref_audio=ref_audio, ref_text=ref_text,
                                          language=language)
            return engine.generate(text, ref_audio=ref_audio, ref_text=ref_text,
                                   language=language, speed_native=native_speed)

        def work(row):
            if self.stop_event.is_set():
                self.set_row(row["iid"], status="Stopped")
                return
            out_path = outdir / f"{row['idx']}.wav"
            # RESUME: da co file day du -> bo qua (chay tiep sau khi dung/crash)
            if self.var_resume.get() and out_path.exists() and out_path.stat().st_size > 0:
                self.set_row(row["iid"], status="Da co (bo qua)")
                self.done_count += 1
                self.refresh_status()
                return
            self.pause_event.wait()
            if self.stop_event.is_set():
                self.set_row(row["iid"], status="Stopped")
                return
            vid = id_q.get()
            try:
                self.set_row(row["iid"], voice=vid, status="Generating...")
                t0 = time.time()
                a, sr = gen_line(raw_gen, row["content"], log=self.log)
                audio = apply_fx(a, sr, fx_speed, pitch)
                # Ghi an toan: viet .part roi doi ten -> crash giua chung khong
                # de lai .wav hong ma Resume tuong la "da xong".
                tmp = out_path.parent / (out_path.name + ".part")
                with open(tmp, "wb") as f:
                    f.write(audio)
                os.replace(tmp, out_path)
                dt = time.time() - t0
                self.set_row(row["iid"], status=f"Done ({dt:.1f}s)")
                self.done_count += 1
                self.refresh_status()
            except Exception as e:
                self.set_row(row["iid"], status="Loi")
                self.log(f"[LOI] dong {row['idx']}: {e}")
            finally:
                id_q.put(vid)

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = [ex.submit(work, row) for row in rows]
            for f in futures:
                try:
                    f.result()
                except Exception:
                    pass

    def on_close(self):
        try:
            self.stop_event.set()
            self.pause_event.set()
        except Exception:
            pass
        # tat server (neu do GUI khoi dong) de giai phong VRAM
        for srv in (self.wsl, self.fish):
            if srv is not None:
                try:
                    srv.stop()
                except Exception:
                    pass
        self.root.destroy()


def _main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except Exception:
        pass
    root.withdraw()                      # an cua so chinh khi dang nhap
    # Tu dong cap nhat (khong chan tool neu loi mang)
    try:
        import updater
        updater.cleanup_temp_installer()
        if updater.maybe_update(root):
            root.destroy()
            return
    except Exception:
        pass
    auth = login_gate(root)
    if not auth:                          # thoat man dang nhap -> khong vao tool
        root.destroy()
        return
    root.deiconify()
    App(root, auth=auth)
    root.mainloop()


def main():
    """Bao boc _main: neu crash -> HIEN hop thoai loi + ghi tool_error.txt
    (tranh tat im khi chay bang pythonw)."""
    try:
        _main()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(here, "tool_error.txt"), "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        try:
            from tkinter import messagebox as _mb
            _mb.showerror("Tool Voice Clone - Loi khoi dong",
                          "Tool gap loi khi mo. Gui file tool_error.txt cho admin.\n\n"
                          + tb[-1500:])
        except Exception:
            pass


if __name__ == "__main__":
    main()
