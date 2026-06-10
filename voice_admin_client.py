# -*- coding: utf-8 -*-
"""Goi cac ham RPC quan tri Voice tren Supabase (dung chung _rpc cua voice_auth).
Moi ham voice_admin_* tren server tu kiem token -> khong lo quyen du dung anon key."""
from __future__ import annotations

from voice_auth import _rpc, AuthNetworkError, AuthConfigError  # noqa: F401


def login(username, password):
    return _rpc("voice_admin_login", {"p_username": username, "p_password": password})


def list_users(token):
    return _rpc("voice_admin_list_users", {"p_token": token})


def create_user(token, username, password, months, max_devices):
    return _rpc("voice_admin_create_user", {"p_token": token, "p_username": username,
        "p_password": password, "p_months": int(months), "p_max_devices": int(max_devices)})


def set_months(token, username, months):
    return _rpc("voice_admin_set_months", {"p_token": token, "p_username": username, "p_months": int(months)})


def add_months(token, username, months):
    return _rpc("voice_admin_add_months", {"p_token": token, "p_username": username, "p_months": int(months)})


def set_devices(token, username, max_devices):
    return _rpc("voice_admin_set_devices", {"p_token": token, "p_username": username, "p_max": int(max_devices)})


def reset_devices(token, username):
    return _rpc("voice_admin_reset_devices", {"p_token": token, "p_username": username})


def set_active(token, username, active):
    return _rpc("voice_admin_set_active", {"p_token": token, "p_username": username, "p_active": bool(active)})


def set_password(token, username, newpass):
    return _rpc("voice_admin_set_password", {"p_token": token, "p_username": username, "p_newpass": newpass})


def delete_user(token, username):
    return _rpc("voice_admin_delete_user", {"p_token": token, "p_username": username})
