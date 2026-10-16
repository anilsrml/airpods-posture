# airpods-durus

AirPods kafa sensörüyle duruş takibi. KDE Plasma 6 üst panelinde renkli bir nokta:
🟢 dik · 🟡 eğik · 🔴 15 sn'den uzun kambur ("DİK DUR" bildirimi) · ⚪ durduruldu / bağlı değil.

## Kullanım

Paneldeki noktaya tıkla → **Başlat** → 3 sn dik dur (kalibrasyon). Durdurmak için **Durdur**.
Kalibrasyon kaydıysa: dik otur → **Şu an dik duruyorum**.

## Kurulum

```bash
cp systemd/airpods-durus.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now airpods-durus
kpackagetool6 --type Plasma/Applet --install widget/org.anilsrml.durus
```

Kaldırma: `systemctl --user disable --now airpods-durus`

## Ayarlar

`~/.config/posture/config.toml` (yoksa varsayılanlar):

```toml
threshold_deg = 15     # öne eğim eşiği
slouch_after_s = 15    # kaç sn eğik kalınca kırmızı + bildirim
zero_window_s = 3      # kalibrasyon süresi
# mac = "AA:BB:CC:DD:EE:FF"   # boşsa eşleşmiş ilk AirPods
```

## Geliştirme

```bash
python3 -m unittest                 # servis testleri
node --test widget/tests/*.test.js  # widget testleri
python3 tools/izle.py               # durumu terminalde izle
```

`spike/` AirPods protokolünü keşfetmek için yazılan deneme betiği ve bulgularıdır.
Protokol bilgisi: [LibrePods](https://github.com/librepods-org/librepods) (GPL-3.0).
