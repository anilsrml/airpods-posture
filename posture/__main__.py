"""Servis: python3 -m posture"""
import logging
import threading
import time

from posture.api import Monitor, make_server
from posture.config import load_config
from posture.engine import PostureEngine
from posture.notifier import notify
from posture.sensor import AirPodsLink, find_airpods_mac, is_connected

RETRY_S = 3

log = logging.getLogger("posture")


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
        monitor.wait_until_running()
        if not is_connected(mac):
            time.sleep(RETRY_S)
            continue
        try:
            with AirPodsLink(mac) as link:
                monitor.connected()
                log.info("kafa takibi başladı, kalibrasyon")
                notify("Calibrating", f"Sit upright for {cfg.engine.zero_window_s:.0f} seconds.")
                for g in link.gravity():
                    if not monitor.running:
                        log.info("durduruldu")
                        break
                    if monitor.update(g):
                        log.info("bildirim gönderildi")
                        notify("SIT UP STRAIGHT", f"You have been leaning forward for {seconds:.0f} seconds.")
        except OSError as e:
            log.info("bağlantı bitti: %s", e)
            time.sleep(RETRY_S)
        monitor.disconnected()


if __name__ == "__main__":
    main()
