"""Duruş kararı: yerçekimi vektörü + zaman → durum. Donanım ve saat bilmez."""
import math
from dataclasses import dataclass
from enum import Enum


def pitch_from_gravity(g):
    """Öne eğim açısı (derece). gx'in işareti hangi kulaklığın gönderdiğine bağlı, o yüzden mutlak alınır."""
    return math.degrees(math.atan2(g[1], abs(g[0])))


class State(Enum):
    DISCONNECTED = "disconnected"
    CALIBRATING = "calibrating"
    UPRIGHT = "upright"
    LEANING = "leaning"
    SLOUCHED = "slouched"


@dataclass(frozen=True)
class Config:
    threshold_deg: float = 15.0
    slouch_after_s: float = 15.0
    notify_after_s: float = 0.0
    zero_window_s: float = 3.0


class PostureEngine:
    def __init__(self, config=Config()):
        self.config = config
        self.pitch = None
        self._connected = False
        self.state = State.DISCONNECTED
        self._ref = None
        self._zero_until = None
        self._zero_samples = []
        self._leaning_since = None
        self._notified = False

    def connected(self, t):
        self._connected = True
        self.recalibrate(t)

    def disconnected(self):
        self._connected = False
        self.state = State.DISCONNECTED
        self._ref = None
        self.pitch = None
        self._reset_timers()

    def recalibrate(self, t):
        """Sonraki zero_window_s saniyedeki duruş yeni sıfır olur."""
        if not self._connected:
            return
        self.state = State.CALIBRATING
        self._zero_until = t + self.config.zero_window_s
        self._zero_samples = []
        self._reset_timers()

    def update(self, t, g):
        """Bir örnek işler. Bildirim gönderilmesi gerekiyorsa True döner."""
        if not self._connected:
            return False
        raw = pitch_from_gravity(g)
        if self.state == State.CALIBRATING:
            if t < self._zero_until:
                self._zero_samples.append(raw)
                return False
            zero = self._zero_samples or [raw]
            self._ref = sum(zero) / len(zero)
        self.pitch = raw - self._ref
        if self.pitch < self.config.threshold_deg:
            self._reset_timers()
            self.state = State.UPRIGHT
            return False
        if self._leaning_since is None:
            self._leaning_since = t
        leaning_for = t - self._leaning_since
        self.state = State.SLOUCHED if leaning_for >= self.config.slouch_after_s else State.LEANING
        if not self._notified and leaning_for >= self.config.slouch_after_s + self.config.notify_after_s:
            self._notified = True
            return True
        return False

    def _reset_timers(self):
        self._leaning_since = None
        self._notified = False
