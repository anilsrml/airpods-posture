"""Widget'ın konuştuğu yerel HTTP API (sadece 127.0.0.1)."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Monitor:
    """PostureEngine'i iş parçacıkları arasında güvenle paylaştırır; zamanı kendisi verir."""

    def __init__(self, engine, clock=time.monotonic):
        self._engine = engine
        self._clock = clock
        self._lock = threading.Lock()
        self._running = threading.Event()

    @property
    def running(self):
        return self._running.is_set()

    def start(self):
        self._running.set()

    def stop(self):
        self._running.clear()
        self.disconnected()

    def wait_until_running(self, timeout=None):
        return self._running.wait(timeout)

    def connected(self):
        with self._lock:
            self._engine.connected(self._clock())

    def disconnected(self):
        with self._lock:
            self._engine.disconnected()

    def update(self, g):
        """Bildirim gönderilmesi gerekiyorsa True döner."""
        with self._lock:
            return self._engine.update(self._clock(), g)

    def recalibrate(self):
        with self._lock:
            self._engine.recalibrate(self._clock())

    def snapshot(self):
        with self._lock:
            e = self._engine
            running = self.running
            return {
                "state": e.state.value if running else "stopped",
                "pitch": None if e.pitch is None or not running else round(e.pitch, 1),
                "threshold_deg": e.config.threshold_deg,
            }


def make_server(monitor, port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/state":
                return self._reply(404, {"error": "not found"})
            self._reply(200, monitor.snapshot())

        def do_POST(self):
            action = {"/start": monitor.start, "/stop": monitor.stop,
                      "/recalibrate": monitor.recalibrate}.get(self.path)
            if action is None:
                return self._reply(404, {"error": "not found"})
            action()
            self._reply(200, monitor.snapshot())

        def _reply(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
