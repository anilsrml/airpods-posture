import tempfile
import unittest
from pathlib import Path

from durus.config import load_config
from durus.engine import Config


class LoadConfigTest(unittest.TestCase):
    def test_missing_file_gives_defaults(self):
        cfg = load_config(Path("/nonexistent/config.toml"))
        self.assertEqual(cfg.engine, Config())
        self.assertIsNone(cfg.mac)
        self.assertEqual(cfg.port, 47800)

    def test_file_overrides_values(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('mac = "AA:BB:CC:DD:EE:FF"\nthreshold_deg = 12\nslouch_after_s = 30\n')
        cfg = load_config(Path(f.name))
        self.assertEqual(cfg.mac, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(cfg.engine.threshold_deg, 12)
        self.assertEqual(cfg.engine.slouch_after_s, 30)
        self.assertEqual(cfg.engine.notify_after_s, Config().notify_after_s)


if __name__ == "__main__":
    unittest.main()
