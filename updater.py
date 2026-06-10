# -*- coding: utf-8 -*-
"""Tu dong cap nhat qua GitHub Releases.

Khi mo tool -> goi API release moi nhat cua repo. Co tag MOI hon ban hien tai ->
hoi nguoi dung; bam Cap nhat thi tai Setup.exe (asset cua release) ve chay roi
dong tool. Bam De sau thi vao tool binh thuong.

Cach phat hanh ban moi (cho OWNER):
  1) Sua APP_VERSION trong version.py + AppVer trong installer.iss (vd 1.2.0).
  2) Build lai Setup.exe (ISCC installer.iss).
  3) Tren GitHub repo -> Releases -> Draft a new release:
       - Tag: v1.2.0
       - Upload file Output\ToolVoiceClone_Setup.exe lam asset
       - Publish.
  -> Lan sau user mo tool se thay thong bao cap nhat.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import tempfile
import threading
import queue
import urllib.request

import tkinter as tk
from tkinter import messagebox, ttk

GITHUB_REPO = "DoanhVuTT03/Tool_voice_Clone"
API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
SETUP_PREFIX = "ToolVoiceClone_Setup"

try:
    from version import APP_VERSION
except Exception:
    APP_VERSION = "0.0.0"


def ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None


def cleanup_temp_installer():
    import glob
    try:
        for f in glob.glob(os.path.join(tempfile.gettempdir(), SETUP_PREFIX + "*.exe")):
            try:
                os.remove(f)
            except Exception:
                pass
    except Exception:
        pass


def _ver_tuple(s):
    out = []
    for part in str(s).strip().lstrip("vV").split("."):
        try:
            out.append(int(part))
        except ValueError:
            out.append(0)
    return tuple(out)


def _is_newer(remote, local):
    return _ver_tuple(remote) > _ver_tuple(local)


def check_for_update():
    """Tra dict {version, url, notes} neu co ban MOI; None neu khong / loi (im lang)."""
    try:
        req = urllib.request.Request(API_LATEST, headers={
            "User-Agent": "ToolVoiceClone-Updater",
            "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10, context=ssl_context()) as resp:
            info = json.loads(resp.read().decode("utf-8", "replace"))
        tag = (info.get("tag_name") or "").strip()
        notes = info.get("body", "") or ""
        url = ""
        for a in info.get("assets", []):
            if (a.get("name") or "").lower().endswith(".exe"):
                url = a.get("browser_download_url"); break
        if tag and url and _is_newer(tag, APP_VERSION):
            return {"version": tag.lstrip("vV"), "url": url, "notes": notes}
    except Exception:
        return None
    return None


def _download(url, dest, q):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ToolVoiceClone-Updater",
                                                   "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context()) as resp, open(dest, "wb") as f:
            total = int(resp.headers.get("Content-Length") or 0)
            got = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk); got += len(chunk)
                q.put(("prog", int(got * 100 / total) if total else -1))
        q.put(("done", dest))
    except Exception as e:
        q.put(("err", str(e)))


def _download_with_progress(root, url):
    name = url.split("/")[-1] or (SETUP_PREFIX + ".exe")
    dest = os.path.join(tempfile.gettempdir(), name)
    q = queue.Queue()
    result = {"path": None}
    win = tk.Toplevel(root); win.title("Dang cap nhat"); win.geometry("370x130")
    win.resizable(False, False); win.grab_set()
    ttk.Label(win, text="Dang tai ban cap nhat...", font=("", 10, "bold")).pack(pady=(14, 6))
    bar = ttk.Progressbar(win, length=330, mode="indeterminate"); bar.pack(padx=20); bar.start(12)
    lbl = ttk.Label(win, text=""); lbl.pack(pady=4)
    threading.Thread(target=_download, args=(url, dest, q), daemon=True).start()

    def poll():
        try:
            while True:
                kind, val = q.get_nowait()
                if kind == "prog" and val >= 0:
                    bar.config(mode="determinate"); bar.stop(); bar["value"] = val
                    lbl.config(text=f"{val}%")
                elif kind == "done":
                    result["path"] = val; win.destroy(); return
                elif kind == "err":
                    messagebox.showerror("Loi cap nhat", f"Khong tai duoc ban moi:\n{val}", parent=win)
                    win.destroy(); return
        except queue.Empty:
            pass
        win.after(100, poll)

    win.after(100, poll)
    root.wait_window(win)
    return result["path"]


def maybe_update(root):
    """Kiem tra + hoi cap nhat. Tra True neu DANG cap nhat (caller nen thoat tool)."""
    info = check_for_update()
    if not info:
        return False
    msg = (f"Da co ban moi: phien ban {info['version']}\n"
           f"(ban hien tai: {APP_VERSION})\n\n{info.get('notes', '')}\n\nCap nhat ngay bay gio?")
    if not messagebox.askyesno("Co ban cap nhat", msg):
        return False
    path = _download_with_progress(root, info["url"])
    if not path or not os.path.isfile(path):
        return False
    messagebox.showinfo("Cap nhat", "Tool se DONG de cai ban moi.\nCai xong hay mo lai tool.")
    try:
        os.startfile(path)
    except Exception as e:
        messagebox.showerror("Loi", f"Khong mo duoc file cai dat:\n{e}")
        return False
    return True
