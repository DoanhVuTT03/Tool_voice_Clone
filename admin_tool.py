# -*- coding: utf-8 -*-
"""Tool ADMIN (chi Doanhbadboiz dung) - quan ly tai khoan Tool Voice Clone tren Supabase.
Dang nhap admin -> Tao/Gia han/Dat han/So thiet bi (+/-)/Reset may/Khoa-Mo/Doi MK/Xoa.
Chay: python admin_tool.py  (hoac Chay_Admin.bat)
KHONG di kem ban cai cho user.
"""
import os
import sys
from datetime import datetime, timezone

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import voice_admin_client as ac

HERE = (getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(HERE, "app.ico")


def _set_icon(win):
    try:
        win.iconbitmap(ICON)
    except Exception:
        pass


def _parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).strip().replace("Z", "+00:00")) if s else None
    except Exception:
        return None


def _fmt_remaining(exp, now):
    if not exp or not now:
        return "?"
    sec = int((exp - now).total_seconds())
    if sec <= 0:
        return "HET HAN"
    d, r = divmod(sec, 86400); h = r // 3600
    return f"{d} ngay {h} gio" if d else f"{h} gio"


class AdminApp:
    def __init__(self, root, token, admin_name):
        self.root = root
        self.token = token
        self.user_info = {}          # username -> {max, count}
        root.title(f"Quan ly tai khoan - Admin: {admin_name}")
        root.geometry("980x600")
        _set_icon(root)

        top = ttk.Frame(root, padding=8); top.pack(fill="x")
        ttk.Label(top, text=f"\U0001F451 Admin: {admin_name}", font=("", 12, "bold")).pack(side="left")
        ttk.Button(top, text="\U0001F504 Lam moi", command=self.refresh).pack(side="right", padx=2)
        ttk.Button(top, text="➕ Tao tai khoan", command=self.create_user).pack(side="right", padx=2)

        mid = ttk.Frame(root, padding=(8, 0)); mid.pack(fill="both", expand=True)
        cols = ("username", "expire", "remain", "active", "devices", "created")
        heads = {"username": "Tai khoan", "expire": "Het han", "remain": "Con lai",
                 "active": "Trang thai", "devices": "Thiet bi (dung/toi da)", "created": "Ngay tao"}
        widths = {"username": 150, "expire": 150, "remain": 110, "active": 90,
                  "devices": 150, "created": 130}
        tv = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            tv.heading(c, text=heads[c])
            tv.column(c, width=widths[c], anchor=("center" if c in ("remain", "active", "devices") else "w"))
        tv.tag_configure("expired", background="#ffe0e0")
        tv.tag_configure("locked", foreground="#9aa0a6")
        sb = ttk.Scrollbar(mid, orient="vertical", command=tv.yview); tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.tv = tv

        # --- thanh nut: so thiet bi +/- + cac chuc nang ---
        bar = ttk.Frame(root, padding=8); bar.pack(fill="x")
        dev = ttk.LabelFrame(bar, text="So thiet bi", padding=4)
        dev.pack(side="left", padx=(0, 10))
        ttk.Button(dev, text="➖", width=3, command=lambda: self._dev(-1)).pack(side="left", padx=2)
        ttk.Button(dev, text="➕", width=3, command=lambda: self._dev(1)).pack(side="left", padx=2)

        ttk.Button(bar, text="\U0001F4C5 Dat han (tu nay + thang)", command=lambda: self._months("set")).pack(side="left", padx=2)
        ttk.Button(bar, text="➕ Gia han them (thang)", command=lambda: self._months("add")).pack(side="left", padx=2)
        ttk.Button(bar, text="\U0001F4BB Reset may", command=self.reset_devices).pack(side="left", padx=2)
        ttk.Button(bar, text="\U0001F512 Khoa", command=lambda: self._active(False)).pack(side="left", padx=2)
        ttk.Button(bar, text="\U0001F513 Mo", command=lambda: self._active(True)).pack(side="left", padx=2)
        ttk.Button(bar, text="\U0001F511 Doi mat khau", command=self.set_password).pack(side="left", padx=2)
        ttk.Button(bar, text="\U0001F5D1 Xoa", command=self.delete_user).pack(side="left", padx=2)

        self.status = ttk.Label(root, text="", foreground="#0a7"); self.status.pack(anchor="w", padx=10, pady=(0, 6))
        self.refresh()

    # -------------------------------------------------------------- #
    def _selected(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Chon", "Hay chon 1 tai khoan trong bang."); return None
        return sel[0]   # iid = username

    def _call(self, fn, *a, ok_msg=None):
        self.status.config(text="Dang xu ly...", foreground="#444")
        self.root.update_idletasks()
        try:
            r = fn(self.token, *a)
        except Exception as e:
            self.status.config(text=f"Loi: {e}", foreground="red")
            messagebox.showerror("Loi", str(e)); return
        if not r.get("ok"):
            self.status.config(text=r.get("reason", "That bai"), foreground="red")
            messagebox.showwarning("Khong thanh cong", r.get("reason", "That bai")); return
        self.status.config(text=ok_msg or "Xong", foreground="#0a7")
        self.refresh()

    # -------------------------------------------------------------- #
    def refresh(self):
        self.status.config(text="Dang tai...", foreground="#444")
        self.root.update_idletasks()
        try:
            r = ac.list_users(self.token)
        except Exception as e:
            self.status.config(text=f"Loi: {e}", foreground="red")
            messagebox.showerror("Loi", str(e)); return
        self._fill(r)

    def _fill(self, r):
        if not r.get("ok"):
            messagebox.showerror("Loi", r.get("reason", "Khong tai duoc")); return
        now = _parse_ts(r.get("server_now")) or datetime.now(timezone.utc)
        self.tv.delete(*self.tv.get_children())
        self.user_info = {}
        for u in r.get("users", []):
            exp = _parse_ts(u.get("expires_at"))
            tags = []
            if exp and exp < now: tags.append("expired")
            if not u.get("active"): tags.append("locked")
            exp_txt = exp.astimezone().strftime("%d/%m/%Y %H:%M") if exp else "?"
            created = _parse_ts(u.get("created_at"))
            mx = int(u.get("max_devices", 1)); cnt = int(u.get("device_count", 0))
            self.user_info[u["username"]] = {"max": mx, "count": cnt}
            self.tv.insert("", "end", iid=u["username"], tags=tags, values=(
                u["username"], exp_txt, _fmt_remaining(exp, now),
                "Hoat dong" if u.get("active") else "Bi khoa",
                f"{cnt} / {mx}",
                created.astimezone().strftime("%d/%m/%Y") if created else ""))
        self.status.config(text=f"Tong: {len(r.get('users', []))} tai khoan", foreground="#0a7")

    # -------------------------------------------------------------- #
    def create_user(self):
        un = simpledialog.askstring("Tao tai khoan", "Ten tai khoan:", parent=self.root)
        if not un or not un.strip():
            return
        pw = simpledialog.askstring("Tao tai khoan", f"Mat khau cho '{un.strip()}':", parent=self.root)
        if not pw:
            return
        m = simpledialog.askinteger("Tao tai khoan", "So thang su dung:", parent=self.root,
                                    minvalue=1, maxvalue=120, initialvalue=1)
        if not m:
            return
        nd = simpledialog.askinteger("Tao tai khoan", "So thiet bi cho phep (so may dang nhap):",
                                     parent=self.root, minvalue=1, maxvalue=50, initialvalue=1)
        if not nd:
            return
        self._call(ac.create_user, un.strip(), pw, m, nd,
                   ok_msg=f"Da tao '{un.strip()}' ({m} thang, {nd} may)")

    def _dev(self, delta):
        u = self._selected()
        if not u:
            return
        info = self.user_info.get(u, {"max": 1})
        new_max = max(1, int(info.get("max", 1)) + delta)
        self._call(ac.set_devices, u, new_max, ok_msg=f"'{u}' -> {new_max} thiet bi")

    def _months(self, mode):
        u = self._selected()
        if not u:
            return
        label = "Dat han = tu nay + (thang):" if mode == "set" else "Gia han them (thang):"
        m = simpledialog.askinteger("So thang", label, parent=self.root,
                                    minvalue=1, maxvalue=120, initialvalue=1)
        if not m:
            return
        fn = ac.set_months if mode == "set" else ac.add_months
        self._call(fn, u, m, ok_msg=f"Da cap nhat han cho '{u}'")

    def reset_devices(self):
        u = self._selected()
        if u and messagebox.askyesno("Reset may",
                f"Bo TAT CA may da dang ky cho '{u}'?\n(Khach dang nhap may moi se khoa lai.)"):
            self._call(ac.reset_devices, u, ok_msg=f"Da reset may cho '{u}'")

    def _active(self, active):
        u = self._selected()
        if u:
            self._call(ac.set_active, u, active, ok_msg=("Da mo" if active else "Da khoa") + f" '{u}'")

    def set_password(self):
        u = self._selected()
        if not u:
            return
        pw = simpledialog.askstring("Doi mat khau", f"Mat khau moi cho '{u}':", parent=self.root)
        if pw:
            self._call(ac.set_password, u, pw, ok_msg=f"Da doi mat khau '{u}'")

    def delete_user(self):
        u = self._selected()
        if u and messagebox.askyesno("Xoa", f"XOA tai khoan '{u}'? Khong khoi phuc duoc."):
            self._call(ac.delete_user, u, ok_msg=f"Da xoa '{u}'")


def run_admin_login(root):
    result = {"token": None, "name": None}
    win = tk.Toplevel(root); win.title("Dang nhap ADMIN"); win.geometry("400x230")
    win.resizable(False, False); win.grab_set(); _set_icon(win)
    frm = ttk.Frame(win, padding=18); frm.pack(fill="both", expand=True)
    ttk.Label(frm, text="\U0001F451 DANG NHAP ADMIN", font=("", 14, "bold")).pack(pady=(0, 12))
    u = tk.StringVar(); p = tk.StringVar()
    r1 = ttk.Frame(frm); r1.pack(fill="x", pady=3)
    ttk.Label(r1, text="Admin:", width=10).pack(side="left")
    e = ttk.Entry(r1, textvariable=u); e.pack(side="left", fill="x", expand=True)
    r2 = ttk.Frame(frm); r2.pack(fill="x", pady=3)
    ttk.Label(r2, text="Mat khau:", width=10).pack(side="left")
    ttk.Entry(r2, textvariable=p, show="*").pack(side="left", fill="x", expand=True)
    msg = ttk.Label(frm, text="", foreground="red", wraplength=350); msg.pack(pady=6)
    btn = ttk.Button(frm, text="Dang nhap"); btn.pack(pady=4)

    def do_login(*_a):
        un, pw = u.get().strip(), p.get()
        if not un or not pw:
            msg.config(text="Nhap tai khoan va mat khau."); return
        btn.config(state="disabled"); msg.config(text="Dang dang nhap...", foreground="#444")
        win.update_idletasks()
        try:
            r = ac.login(un, pw)
        except Exception as ex:
            msg.config(text=str(ex), foreground="red"); btn.config(state="normal"); return
        if r.get("ok"):
            result["token"] = r["token"]; result["name"] = r.get("username", un); win.destroy()
        else:
            msg.config(text=r.get("reason", "That bai"), foreground="red"); btn.config(state="normal")

    btn.config(command=do_login); win.bind("<Return>", do_login)
    win.protocol("WM_DELETE_WINDOW", win.destroy); e.focus_set()
    root.wait_window(win)
    return result["token"], result["name"]


if __name__ == "__main__":
    try:
        root = tk.Tk(); root.withdraw()
        try:
            ttk.Style().theme_use("vista")
        except Exception:
            pass
        token, name = run_admin_login(root)
        if not token:
            root.destroy()
        else:
            AdminApp(root, token, name); root.deiconify(); root.mainloop()
    except Exception as e:
        try:
            messagebox.showerror("Loi", str(e))
        except Exception:
            print(e)
