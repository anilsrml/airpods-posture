#!/usr/bin/env python3
"""Servisin durumunu terminalde saniyede 2 kez gösterir (widget gelene kadar)."""
import json
import time
import urllib.request

LABELS = {
    "upright": ("🟢", "DİK"), "leaning": ("🟡", "EĞİK"), "slouched": ("🔴", "KAMBUR"),
    "calibrating": ("⚪", "SIFIRLANIYOR, dik dur"), "disconnected": ("⚪", "AirPods bağlı değil"),
    "paused": ("⚪", "DURAKLATILDI"),
}
since, last = time.monotonic(), None
while True:
    try:
        with urllib.request.urlopen("http://127.0.0.1:47800/state", timeout=1) as r:
            s = json.load(r)
        if s["state"] != last:
            since, last = time.monotonic(), s["state"]
        icon, text = LABELS[s["state"]]
        pitch = "" if s["pitch"] is None else f"öne eğim {s['pitch']:+6.1f}°"
        line = f"{icon} {text:<22s} {pitch}   ({time.monotonic() - since:4.0f} sn)"
    except OSError:
        line = "❌ servis çalışmıyor"
    print(f"\r{line:<70s}", end="", flush=True)
    time.sleep(0.5)
