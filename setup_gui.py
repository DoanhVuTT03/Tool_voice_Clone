# -*- coding: utf-8 -*-
"""Cua so CAI DAT co tien trinh (thay cua so den cmd).
Chay boi Python 3.11 he thong (cai_dat.bat goi sau khi da co Python).
Cac buoc: tao .venv -> pip -> PyTorch -> OmniVoice/thu vien -> TAI SAN MODEL.
"""
import os
import sys
import shutil
import subprocess
import threading
import queue

import tkinter as tk
from tkinter import ttk, messagebox

APPDIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(APPDIR)
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
PIP_OPTS = ["--retries", "10", "--timeout", "120"]


def sys_python():
    """Python 3.11 he thong (tham so 1 do cai_dat truyen, hoac tu do)."""
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        return sys.argv[1]
    cand = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python311", "python.exe")
    if os.path.isfile(cand):
        return cand
    return shutil.which("python") or sys.executable


def vpy():
    return os.path.join(APPDIR, ".venv", "Scripts", "python.exe")


class SetupGUI:
    STEPS = 5

    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.done = False
        root.title("Cai dat Tool Voice Clone (Doanhbadboiz)")
        root.geometry("620x430")
        try:
            root.iconbitmap(os.path.join(APPDIR, "app.ico"))
        except Exception:
            pass

        tk.Label(root, text="Dang cai dat Tool Voice Clone",
                 font=("Segoe UI", 13, "bold")).pack(pady=(14, 2))
        tk.Label(root, text="Lan dau se tai thu vien + model (~vai GB). Can internet, vui long doi.",
                 fg="#666").pack()

        self.lbl_step = tk.Label(root, text="Chuan bi...", font=("Segoe UI", 10, "bold"), fg="#2563EB")
        self.lbl_step.pack(pady=(12, 4))
        self.bar = ttk.Progressbar(root, length=560, mode="indeterminate")
        self.bar.pack(padx=20)
        self.bar.start(12)
        self.lbl_overall = tk.Label(root, text="", fg="#666")
        self.lbl_overall.pack(pady=(4, 6))

        frm = tk.Frame(root)
        frm.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self.txt = tk.Text(frm, height=11, wrap="word", bg="#0b1020", fg="#cbd5e1",
                           font=("Consolas", 9), insertbackground="#cbd5e1")
        sb = ttk.Scrollbar(frm, command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)
        self.txt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        btns = tk.Frame(root); btns.pack(fill="x", padx=20, pady=(0, 10))
        self.btn_open = ttk.Button(btns, text="Mo Tool", command=self._open_tool, state="disabled")
        self.btn_open.pack(side="right", padx=4)
        self.btn_close = ttk.Button(btns, text="Dong", command=root.destroy)
        self.btn_close.pack(side="right", padx=4)

        threading.Thread(target=self._worker, daemon=True).start()
        root.after(100, self._poll)

    # ----- helpers -----
    def _log(self, s):
        self.q.put(("log", s))

    def _step(self, i, label):
        self.q.put(("step", i, label))

    def _run(self, cmd):
        """Chay 1 lenh, day output vao log. Tra ve returncode."""
        self._log("> " + " ".join(os.path.basename(c) if c == cmd[0] else c for c in cmd))
        try:
            p = subprocess.Popen(cmd, cwd=APPDIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                                 errors="replace", bufsize=1, creationflags=NOWIN,
                                 env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        except Exception as e:
            self._log(f"[LOI] {e}")
            return 1
        for line in p.stdout:
            line = line.rstrip()
            if line:
                self._log(line)
        p.wait()
        return p.returncode

    # ----- worker (luong nen) -----
    def _worker(self):
        py = sys_python()
        self._log(f"Python he thong: {py}")

        self._step(1, "Tao moi truong ao (.venv)")
        if not os.path.isfile(vpy()):
            if self._run([py, "-m", "venv", ".venv"]) != 0 or not os.path.isfile(vpy()):
                return self.q.put(("err", "Tao .venv that bai."))

        self._step(2, "Nang cap pip")
        self._run([vpy(), "-m", "pip", "install", "--upgrade", "pip"])

        self._step(3, "Cai PyTorch (GPU CUDA 12.8) - co the tai 2-3GB")
        rc = self._run([vpy(), "-m", "pip", "install"] + PIP_OPTS +
                       ["torch==2.8.0+cu128", "torchaudio==2.8.0+cu128",
                        "--extra-index-url", "https://download.pytorch.org/whl/cu128"])
        if rc != 0:
            self._log("Ban GPU loi -> thu ban CPU...")
            if self._run([vpy(), "-m", "pip", "install"] + PIP_OPTS +
                         ["torch==2.8.0", "torchaudio==2.8.0"]) != 0:
                return self.q.put(("err", "Cai PyTorch that bai (xem log)."))

        self._step(4, "Cai OmniVoice + thu vien")
        if self._run([vpy(), "-m", "pip", "install"] + PIP_OPTS + ["-r", "requirements.txt"]) != 0:
            return self.q.put(("err", "Cai thu vien that bai (xem log)."))

        self._step(5, "Tai san model OmniVoice (VN + Base) - ~vai GB")
        self._run([vpy(), "download_models.py"])   # loi tai model khong chan (tai lai khi can)

        self.q.put(("done", None))

    # ----- cap nhat UI -----
    def _poll(self):
        try:
            while True:
                item = self.q.get_nowait()
                kind = item[0]
                if kind == "log":
                    self.txt.insert("end", item[1] + "\n")
                    self.txt.see("end")
                elif kind == "step":
                    i, label = item[1], item[2]
                    self.lbl_step.config(text=f"Buoc {i}/{self.STEPS}: {label}")
                    self.lbl_overall.config(text=f"({i}/{self.STEPS})")
                elif kind == "done":
                    self._finish_ok()
                    return
                elif kind == "err":
                    self._finish_err(item[1])
                    return
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _finish_ok(self):
        self.done = True
        self.bar.stop(); self.bar.config(mode="determinate", value=100)
        self.lbl_step.config(text="✓ CAI DAT HOAN TAT!", fg="#16a34a")
        self.lbl_overall.config(text="San sang dung. Bam 'Mo Tool'.")
        self.btn_open.config(state="normal")

    def _finish_err(self, msg):
        self.bar.stop()
        self.lbl_step.config(text="✗ Cai dat chua xong", fg="#dc2626")
        self.lbl_overall.config(text=msg)
        messagebox.showerror("Cai dat loi", f"{msg}\n\nXem log ben duoi. Co the do rot mang -> "
                                            f"dong cua so va chay lai cai_dat.bat (no tai tiep).")

    def _open_tool(self):
        try:
            pw = os.path.join(APPDIR, ".venv", "Scripts", "pythonw.exe")
            subprocess.Popen([pw, os.path.join(APPDIR, "tts_gui.py")], cwd=APPDIR,
                             creationflags=NOWIN)
        except Exception as e:
            messagebox.showerror("Loi", str(e))
        self.root.destroy()


def main():
    try:
        root = tk.Tk()
        try:
            ttk.Style().theme_use("vista")
        except Exception:
            pass
        SetupGUI(root)
        root.mainloop()
    except Exception:
        # GUI khong chay duoc -> ghi log de chan doan; cai_dat.bat se tu lui ve CLI.
        import traceback
        try:
            with open(os.path.join(APPDIR, "setup_error.txt"), "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
