import logging, time
import requests
from config.settings import settings

log = logging.getLogger(__name__)


class SourceUnavailable(Exception):
    pass


def get_json(url: str, params: dict) -> dict:
    last = None
    for attempt in range(settings.http_retries):
        try:
            r = requests.get(url, params=params, timeout=settings.http_timeout_s,
                             headers={"User-Agent": "FieldShift/0.1 (NASA Space Apps 2026)"})
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
            if r.status_code < 500 and r.status_code != 429:
                break
        except requests.RequestException as e:
            last = type(e).__name__
        time.sleep(1.5 * (attempt + 1))
    log.warning("Fuente no disponible: %s (%s)", url, last)
    raise SourceUnavailable(last)
