#!/usr/bin/env python3
"""AirPods kafa sensörü deneme betiği (atılacak kod, test yok).

Protokol: LibrePods "AAP Definitions" dokümanı (GPL-3.0).
https://github.com/librepods-org/librepods/blob/main/docs/AAP%20Definitions.md

AirPods 4 (firmware 2026-10) bulguları:
  - Sadece yeni başlatma paketi (START) çalışıyor; eski paket sadece cihaz tanımı döndürüyor.
  - ~25 Hz. Paket uzunluğu 80/81 bayt (sıra no varint), bu yüzden sabit ofset yerine
    PAYLOAD_MARK'tan sonraki 58 baytlık yük okunur.
  - Yük[20:26] ham ivme (int16 x3, |a|~26000), yük[26:32] jiroskop,
    yük[44:50] yerçekimi birim vektörü x1024 (|g|~1022, mutlak).
  - Öne eğim = atan2(gy, |gx|); gx işareti hangi kulaklığın veri gönderdiğine göre değişir.
  - Yeniden takma testi (5 takış): dik duruşta öne eğim 44-53° arası (std 3.0°).
    Sonuç: mutlak açıya güvenilmez, her takışta sıfırlama gerekir.

Kullanım:
  python3 spike.py live              # canlı yerçekimi vektörü ve eğim
  python3 spike.py guided            # yönlendirmeli hareket kaydı (25 sn)
  python3 spike.py measure ETIKET    # 5 sn dik duruş kaydı (yeniden takma testi)
  python3 spike.py analyze           # yeniden takma ölçümlerini karşılaştır
"""
import json
import math
import os
import socket
import struct
import sys
import time
from pathlib import Path

MAC = os.environ.get("AIRPODS_MAC", "AA:BB:CC:DD:EE:FF")  # bluetoothctl devices
PSM = 0x1001
DATA_DIR = Path(__file__).parent / "data"

HANDSHAKE = bytes.fromhex("00000400010002000000000000000000")
START = bytes.fromhex("040004001700000010000F000873420B081010021A0501409C0000")
STOP = bytes.fromhex("040004001700000010001100087E1002420B084E10021A050100000000")
PAYLOAD_MARK = bytes.fromhex("3a3e08101a3a")
PAYLOAD_LEN = 58


def open_stream():
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
    s.settimeout(5)
    s.connect((MAC, PSM))
    s.send(HANDSHAKE)
    s.settimeout(0.5)
    end = time.time() + 2  # açılış paketlerini boşalt
    while time.time() < end:
        try:
            s.recv(2048)
        except socket.timeout:
            pass
    s.send(START)
    return s


def close_stream(s):
    try:
        s.send(STOP)
    finally:
        s.close()


def samples(s, seconds=None):
    """(zaman, ivme, jiro, yerçekimi) üretir."""
    t0 = time.time()
    while seconds is None or time.time() - t0 < seconds:
        try:
            pkt = s.recv(2048)
        except socket.timeout:
            continue
        i = pkt.find(PAYLOAD_MARK)
        if i < 0 or len(pkt) < i + 6 + PAYLOAD_LEN:
            continue
        p = pkt[i + 6:i + 6 + PAYLOAD_LEN]
        yield (time.time() - t0,
               struct.unpack_from("<hhh", p, 20),
               struct.unpack_from("<hhh", p, 26),
               struct.unpack_from("<hhh", p, 44))


def angle(u, v):
    dot = sum(a * b for a, b in zip(u, v))
    cos = dot / (math.dist(u, (0, 0, 0)) * math.dist(v, (0, 0, 0)))
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def pitch_roll(g):
    """guided testinden: öne eğilme g'yi x-y düzleminde döndürüyor, yana yatma z'yi değiştiriyor."""
    pitch = math.degrees(math.atan2(g[1], g[0]))
    roll = math.degrees(math.asin(max(-1.0, min(1.0, g[2] / math.dist(g, (0, 0, 0))))))
    return pitch, roll


def cmd_live(hz=2):
    s = open_stream()
    ref, buf, next_t = None, [], 1.0
    green, yellow, red, reset = "\033[32m", "\033[33m", "\033[31m", "\033[0m"
    try:
        print("İlk 1 sn dik dur (referans alınıyor)…", flush=True)
        for t, a, w, g in samples(s):
            buf.append(g)
            if t < next_t:
                continue
            next_t += 1 / hz
            m = [sum(c) / len(buf) for c in zip(*buf)]
            buf = []
            p, r = pitch_roll(m)
            if ref is None:
                ref = p
                print(f"Referans: {ref:.1f}°  (Ctrl-C ile çık)\n", flush=True)
                continue
            d = p - ref
            color = green if d < 10 else yellow if d < 15 else red
            bar = "█" * max(0, min(30, round(d)))
            print(f"\r{color}öne eğim {d:+6.1f}°  {bar:<30s}{reset}  yana {r:+5.1f}°  "
                  f"(mutlak {p:5.1f}°)", end="", flush=True)
    except KeyboardInterrupt:
        print()
    finally:
        close_stream(s)


STAGES = [("DİK otur", 5), ("başını ÖNE eğ (telefona bakar gibi)", 5), ("DİK otur", 5),
          ("başını SAĞA yatır (kulak omza)", 5), ("DİK otur", 5)]


def cmd_guided():
    DATA_DIR.mkdir(exist_ok=True)
    input("25 sn sürecek, ekrandaki yönergeleri izle. Hazırsan Enter'a bas…")
    s = open_stream()
    rows = []
    try:
        for label, secs in STAGES:
            print(f"\n>>> {label}  ({secs} sn)", flush=True)
            for t, a, w, g in samples(s, secs):
                rows.append({"stage": label, "a": a, "w": w, "g": g})
    finally:
        close_stream(s)
    out = DATA_DIR / "guided.json"
    out.write_text(json.dumps(rows))
    print(f"\nBitti: {len(rows)} örnek → {out}")


def cmd_measure(label):
    DATA_DIR.mkdir(exist_ok=True)
    s = open_stream()
    try:
        print("Dik otur, 5 sn ölçülüyor…", flush=True)
        g = [g for _, _, _, g in samples(s, 5)]
    finally:
        close_stream(s)
    mean = [sum(c) / len(g) for c in zip(*g)]
    out = DATA_DIR / f"measure-{int(time.time())}-{label}.json"
    out.write_text(json.dumps({"label": label, "g": mean, "n": len(g)}))
    print(f"g=({mean[0]:.0f},{mean[1]:.0f},{mean[2]:.0f}) → {out.name}")


def cmd_analyze():
    ms = [json.loads(f.read_text()) for f in sorted(DATA_DIR.glob("measure-*.json"))]
    if len(ms) < 2:
        raise SystemExit("En az 2 ölçüm gerekli.")
    ref = [sum(c) / len(ms) for c in zip(*(m["g"] for m in ms))]
    for m in ms:
        print(f"{m['label']:10s} ortalamadan sapma = {angle(m['g'], ref):4.1f}°")
    worst = max(angle(a["g"], b["g"]) for a in ms for b in ms)
    print(f"En büyük fark: {worst:.1f}°  → {'MUTLAK (tek kalibrasyon yeter)' if worst < 3 else 'kayma var'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "live"
    if cmd == "live":
        cmd_live()
    elif cmd == "guided":
        cmd_guided()
    elif cmd == "measure":
        cmd_measure(sys.argv[2] if len(sys.argv) > 2 else "dik")
    elif cmd == "analyze":
        cmd_analyze()
    else:
        raise SystemExit(__doc__)
