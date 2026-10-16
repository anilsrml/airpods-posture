"""AirPods kafa sensörü (AAP, L2CAP PSM 0x1001).

Paket yapısı LibrePods "AAP Definitions" dokümanından ve spike ölçümlerinden.
"""
import struct

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
