"""KDE bildirimi (freedesktop notify-send)."""
import subprocess


def notify(summary, body):
    subprocess.run(["notify-send", "-a", "Duruş", "-i", "dialog-warning", summary, body], check=False)
