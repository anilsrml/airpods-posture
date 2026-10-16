"""~/.config/posture/config.toml okuma. Dosya yoksa varsayılanlar."""
import dataclasses
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from posture.engine import Config

DEFAULT_PATH = Path.home() / ".config" / "posture" / "config.toml"


@dataclass(frozen=True)
class AppConfig:
    mac: str | None = None
    port: int = 47800
    engine: Config = field(default_factory=Config)


def load_config(path=DEFAULT_PATH):
    try:
        data = tomllib.loads(path.read_text())
    except FileNotFoundError:
        return AppConfig()
    engine_keys = {f.name for f in dataclasses.fields(Config)}
    engine = Config(**{k: v for k, v in data.items() if k in engine_keys})
    return AppConfig(mac=data.get("mac"), port=data.get("port", 47800), engine=engine)
