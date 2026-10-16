"""AirPods kafa sensörü (AAP, L2CAP PSM 0x1001).

Paket yapısı LibrePods "AAP Definitions" dokümanından ve spike ölçümlerinden.
"""
import socket
import struct
import subprocess
import time

PAYLOAD_MARK = bytes.fromhex("3a3e08101a3a")
PAYLOAD_LEN = 58
GRAVITY_OFFSET = 44


def parse_gravity(pkt):
    """Kafa takibi paketinden yerçekimi vektörünü (int16 x3, ~1024 birim) döndürür.

    Başka paketler, eksik paketler ve sensör ısınırken gelen sıfır vektör için None.
    """
    i = pkt.find(PAYLOAD_MARK)
    if i < 0:
        return None
    payload = pkt[i + len(PAYLOAD_MARK):i + len(PAYLOAD_MARK) + PAYLOAD_LEN]
    if len(payload) < PAYLOAD_LEN:
        return None
    g = struct.unpack_from("<hhh", payload, GRAVITY_OFFSET)
    return None if g == (0, 0, 0) else g


# --- Bluetooth sınırı: birim testi yok, gerçek AirPods ile doğrulanır. ---
PSM = 0x1001
HANDSHAKE = bytes.fromhex("00000400010002000000000000000000")
START = bytes.fromhex("040004001700000010000F000873420B081010021A0501409C0000")
STOP = bytes.fromhex("040004001700000010001100087E1002420B084E10021A050100000000")
STALL_S = 5.0


def find_airpods_mac():
    out = subprocess.run(["bluetoothctl", "devices", "Paired"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3 and "AirPods" in parts[2]:
            return parts[1]
    return None


def is_connected(mac):
    path = "/org/bluez/hci0/dev_" + mac.replace(":", "_")
    out = subprocess.run(["busctl", "get-property", "org.bluez", path, "org.bluez.Device1", "Connected"],
                         capture_output=True, text=True).stdout
    return out.strip() == "b true"


class AirPodsLink:
    """with bloğu içinde kafa takibi açık; çıkışta kapatılır."""

    def __init__(self, mac):
        self.mac = mac
        self._sock = None

    def __enter__(self):
        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        try:
            s.settimeout(5)
            s.connect((self.mac, PSM))
            s.send(HANDSHAKE)
            s.settimeout(0.5)
            end = time.monotonic() + 1.5  # açılış paketlerini boşalt
            while time.monotonic() < end:
                try:
                    s.recv(2048)
                except socket.timeout:
                    pass
            s.send(START)
        except OSError:
            s.close()
            raise
        self._sock = s
        return self

    def __exit__(self, *exc):
        try:
            self._sock.send(STOP)
        except OSError:
            pass
        self._sock.close()

    def gravity(self):
        """Yerçekimi vektörleri üretir. Bağlantı koparsa ya da veri durursa ConnectionError."""
        last = time.monotonic()
        while True:
            try:
                pkt = self._sock.recv(2048)
            except socket.timeout:
                pkt = None
            if pkt == b"":
                raise ConnectionError("AirPods bağlantıyı kapattı")
            g = parse_gravity(pkt) if pkt else None
            if g is not None:
                last = time.monotonic()
                yield g
            elif time.monotonic() - last > STALL_S:
                raise ConnectionError(f"{STALL_S:.0f} sn sensör verisi gelmedi")
