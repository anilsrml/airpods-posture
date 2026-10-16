import json
import threading
import unittest
import urllib.error
import urllib.request

from durus.api import Monitor, make_server
from durus.engine import PostureEngine
from tests.test_engine import UPRIGHT_PITCH, gravity


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.monitor = Monitor(PostureEngine(), clock=self.clock)
        self.server = make_server(self.monitor, port=0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def get_state(self):
        with urllib.request.urlopen(self.base + "/state") as r:
            return json.load(r)

    def test_service_starts_stopped(self):
        state = self.get_state()
        self.assertEqual(state["state"], "stopped")
        self.assertIsNone(state["pitch"])
        self.assertEqual(state["threshold_deg"], 15.0)

    def post(self, path):
        req = urllib.request.Request(self.base + path, method="POST")
        with urllib.request.urlopen(req) as r:
            return json.load(r)

    def run_for(self, seconds, pitch_deg, hz=25):
        notes = 0
        for _ in range(round(seconds * hz)):
            self.clock.now += 1 / hz
            notes += self.monitor.update(gravity(pitch_deg))
        return notes

    def connect_and_calibrate(self):
        self.post("/start")
        self.monitor.connected()
        self.run_for(3.5, UPRIGHT_PITCH)

    def test_state_shows_pitch_while_leaning(self):
        self.connect_and_calibrate()
        self.run_for(1, UPRIGHT_PITCH + 18)
        state = self.get_state()
        self.assertEqual(state["state"], "leaning")
        self.assertAlmostEqual(state["pitch"], 18.0, places=1)

    def test_start_waits_for_airpods(self):
        self.assertEqual(self.post("/start")["state"], "disconnected")
        self.assertTrue(self.monitor.wait_until_running(timeout=0))

    def test_stop_returns_to_stopped(self):
        self.connect_and_calibrate()
        state = self.post("/stop")
        self.assertEqual(state["state"], "stopped")
        self.assertIsNone(state["pitch"])
        self.assertFalse(self.monitor.running)

    def test_recalibrate_uses_posture_from_now_on(self):
        self.connect_and_calibrate()
        self.assertEqual(self.post("/recalibrate")["state"], "calibrating")
        self.run_for(3.5, UPRIGHT_PITCH + 18)
        self.assertEqual(self.get_state()["state"], "upright")

    def test_unknown_post_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.post("/reboot")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
