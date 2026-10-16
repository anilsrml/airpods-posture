# airpods-durus

Posture monitor for Linux that uses the motion sensor in your AirPods. A dot in the KDE Plasma panel shows whether you are sitting upright, and a notification tells you to sit up when you slouch.

🟢 upright · 🟡 leaning forward · 🔴 slouching for more than 15 s (shows a "DİK DUR" notification) · ⚪ stopped or not connected

## How it works

- AirPods send head-tracking data over Bluetooth (AAP protocol, L2CAP PSM `0x1001`). The protocol was reverse-engineered by [LibrePods](https://github.com/librepods-org/librepods).
- A Python service reads the gravity vector at about 25 Hz and calculates how far your head tilts forward.
- When you press **Başlat** (Start), the service takes your posture during the first 3 seconds as "upright". It does this every time, because the earbud sits at a slightly different angle each time you put it in.
- The Plasma widget reads the state from `http://127.0.0.1:47800/state` twice per second.

## Requirements

- Linux with BlueZ and KDE Plasma 6
- Python 3.11 or later (standard library only)
- AirPods with head tracking. Tested on AirPods 4. AirPods 3, Pro 2 and Pro 3 should also work.

## Install

```bash
cp systemd/airpods-durus.service ~/.config/systemd/user/   # edit WorkingDirectory if needed
systemctl --user daemon-reload
systemctl --user enable --now airpods-durus
kpackagetool6 --type Plasma/Applet --install widget/org.anilsrml.durus
```

Then right-click the panel, select **Add Widgets…** and add **Duruş**.

## Use

1. Click the dot in the panel and press **Başlat** (Start).
2. Sit upright for 3 seconds while it calibrates.
3. If the calibration is off, sit upright and press **Şu an dik duruyorum** ("I am upright now").

## Configuration

`~/.config/posture/config.toml` is optional. These are the defaults:

```toml
threshold_deg = 15    # forward tilt that counts as leaning
slouch_after_s = 15   # seconds of leaning before red + notification
zero_window_s = 3     # calibration time
# mac = "AA:BB:CC:DD:EE:FF"   # default: first paired device named "AirPods"
```

## Development

```bash
python3 -m unittest                  # service tests
node --test widget/tests/*.test.js   # widget tests
python3 tools/izle.py                # live state in the terminal
```

`spike/` contains the script that was used to explore the protocol, with notes on what was found.

## License

GPL-3.0-or-later
