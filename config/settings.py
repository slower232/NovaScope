"""Configuración central. Los secretos se leen SOLO de variables de entorno / .env."""
import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env = BASE_DIR / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("FIELD_SHIFT_DB_PATH", str(BASE_DIR / "field_shift.db"))
    log_level: str = os.getenv("FIELD_SHIFT_LOG_LEVEL", "INFO")
    history_years: int = int(os.getenv("FIELD_SHIFT_HISTORY_YEARS", "15"))
    ttl_power_h: int = int(os.getenv("FIELD_SHIFT_CACHE_TTL_HOURS_POWER", "168"))
    ttl_forecast_h: int = int(os.getenv("FIELD_SHIFT_CACHE_TTL_HOURS_FORECAST", "3"))
    http_timeout_s: int = 60
    http_retries: int = 3
    ai_api_key: str = os.getenv("FIELD_SHIFT_AI_API_KEY", "")
    crops_path: str = str(BASE_DIR / "data" / "crops" / "crops.json")
    weights_path: str = str(BASE_DIR / "data" / "reference" / "rotation_weights.json")
    backups_dir: str = str(BASE_DIR / "backups")


settings = Settings()
