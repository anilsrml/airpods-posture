"""Servis: python3 -m durus"""
import logging
import threading
import time

from durus.api import Monitor, make_server
from durus.config import load_config
from durus.engine import PostureEngine
from durus.notifier import notify
from durus.sensor import AirPodsLink, find_airpods_mac, is_connected

RETRY_S = 3

log = logging.getLogger("durus")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cfg = load_config()
    mac = cfg.mac or find_airpods_mac()
    if mac is None:
        raise SystemExit("Eşleşmiş AirPods bulunamadı; config.toml içinde mac = \"..\" ver.")
    monitor = Monitor(PostureEngine(cfg.engine))
    server = make_server(monitor, cfg.port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("API http://127.0.0.1:%d/state, AirPods %s", cfg.port, mac)

    seconds = cfg.engine.slouch_after_s + cfg.engine.notify_after_s
    while True:
        if not is_connected(mac):
            time.sleep(RETRY_S)
            continue
        try:
            with AirPodsLink(mac) as link:
                monitor.connected()
                log.info("kafa takibi başladı, %.0f sn dik dur", cfg.engine.zero_window_s)
                for g in link.gravity():
                    if monitor.update(g):
                        log.info("bildirim gönderildi")
                        notify("DİK DUR", f"{seconds:.0f} saniyedir öne eğiksin.")
        except OSError as e:
            log.info("bağlantı bitti: %s", e)
        monitor.disconnected()
        time.sleep(RETRY_S)


if __name__ == "__main__":
    main()
