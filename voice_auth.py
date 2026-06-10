# -*- coding: utf-8 -*-
"""Dang nhap Supabase + van tay may (HWID) cho Tool Voice Clone.

Goi RPC: voice_login, voice_validate (xem supabase/voice_setup.sql).
Dung urllib (khong them thu vien). Cau hinh trong auth_config.json.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

_FROZEN = getattr(sys, "frozen", False)
HERE = (getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)) if _FROZEN
        else os.path.dirname(os.path.abspath(__file__)))
_NOWINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

AUTH_CONFIG = os.path.join(HERE, "auth_config.json")


def _data_dir():
    if _FROZEN:
        d = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "ToolVoiceClone")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return d
    return os.path.dirname(os.path.abspath(__file__))


REMEMBER_FILE = os.path.join(_data_dir(), "login_remember.dat")


class AuthNetworkError(Exception):
    """Loi mang / khong goi duoc Supabase."""


class AuthConfigError(Exception):
    """Chua cau hinh auth_config.json."""


def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None


def load_cfg():
    try:
        c = json.load(open(AUTH_CONFIG, encoding="utf-8"))
    except Exception as e:
        raise AuthConfigError(f"Khong doc duoc auth_config.json: {e}")
    url = (c.get("url") or "").strip().rstrip("/")
    key = (c.get("anon_key") or "").strip()
    if not url or not key:
        raise AuthConfigError("Thieu 'url' / 'anon_key' trong auth_config.json.")
    return url, key


# --------------------------------------------------------------------------- #
# HWID - van tay may (dung PowerShell CIM: hop ca Win11 24H2+ da bo wmic)
# --------------------------------------------------------------------------- #
def _ps(cmd):
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                             capture_output=True, text=True, creationflags=_NOWINDOW, timeout=12)
        return (out.stdout or "").strip()
    except Exception:
        return ""


_HWID_CACHE = None


def get_hwid():
    """Chuoi sha256 on dinh nhan dien may."""
    global _HWID_CACHE
    if _HWID_CACHE:
        return _HWID_CACHE
    parts = []
    if os.name == "nt":
        parts.append(_ps("(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"))
        parts.append(_ps("(Get-CimInstance -ClassName Win32_BaseBoard).SerialNumber"))
    try:
        import uuid as _uuid
        parts.append(format(_uuid.getnode(), "x"))
    except Exception:
        pass
    parts.append(os.environ.get("COMPUTERNAME", "") or os.environ.get("HOSTNAME", ""))
    raw = "|".join(p for p in parts if p and p.lower() not in ("", "to be filled by o.e.m.")) or "unknown-machine"
    _HWID_CACHE = hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()
    return _HWID_CACHE


# --------------------------------------------------------------------------- #
# Goi RPC
# --------------------------------------------------------------------------- #
def _rpc(fn, params):
    url, key = load_cfg()
    endpoint = f"{url}/rest/v1/rpc/{fn}"
    req = urllib.request.Request(endpoint, data=json.dumps(params).encode("utf-8"), method="POST")
    req.add_header("apikey", key)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15, context=_ssl_context()) as resp:
            data = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = ""
        raise AuthNetworkError(f"May chu tra loi {e.code}. {detail}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise AuthNetworkError(f"Khong ket noi duoc may chu (kiem tra mang): {e}")
    try:
        return json.loads(data)
    except Exception:
        raise AuthNetworkError(f"Phan hoi khong hop le: {data[:200]}")


def login(username, password):
    return _rpc("voice_login", {"p_username": username, "p_password": password, "p_hwid": get_hwid()})


def validate(username, token):
    return _rpc("voice_validate", {"p_username": username, "p_hwid": get_hwid(), "p_token": token})


# --------------------------------------------------------------------------- #
# Ghi nho dang nhap (ma hoa theo HWID)
# --------------------------------------------------------------------------- #
def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _remember_key() -> bytes:
    return hashlib.sha256(("remember:" + get_hwid()).encode("utf-8")).digest()


def save_remember(username, password):
    try:
        enc = base64.b64encode(_xor(password.encode("utf-8"), _remember_key())).decode("ascii")
        json.dump({"u": username, "p": enc}, open(REMEMBER_FILE, "w", encoding="utf-8"))
    except Exception:
        pass


def load_remember():
    try:
        d = json.load(open(REMEMBER_FILE, encoding="utf-8"))
        pw = _xor(base64.b64decode(d["p"]), _remember_key()).decode("utf-8")
        return d.get("u", ""), pw
    except Exception:
        return None


def clear_remember():
    try:
        if os.path.isfile(REMEMBER_FILE):
            os.remove(REMEMBER_FILE)
    except Exception:
        pass
