import shutil
from datetime import datetime
from pathlib import Path
from config.settings import settings
from database.connection import get_engine
from database.models import Base


def init_db():
    Base.metadata.create_all(get_engine())


def backup_db() -> str | None:
    src = Path(settings.db_path)
    if not src.exists():
        return None
    Path(settings.backups_dir).mkdir(parents=True, exist_ok=True)
    dst = Path(settings.backups_dir) / f"field_shift_{datetime.utcnow():%Y%m%d_%H%M%S}.db"
    shutil.copy2(src, dst)
    return str(dst)
