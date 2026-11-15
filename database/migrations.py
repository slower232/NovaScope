"""Migraciones ligeras para SQLite: agrega columnas faltantes sin borrar datos existentes."""
import sqlite3

NEW_FARM_COLUMNS = {
    "agri_type": "VARCHAR(20)",
    "water_availability": "VARCHAR(20)",
    "irrigation_system": "VARCHAR(60)",
    "crop_history": "TEXT",
    "organic_matter": "FLOAT",
    "preferences": "TEXT",
}


def ensure_columns(conn: sqlite3.Connection, table: str = "farms", columns: dict | None = None) -> list[str]:
    cols = columns or NEW_FARM_COLUMNS
    existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    if not existing:
        return []
    added = []
    for name, ddl in cols.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
            added.append(name)
    conn.commit()
    return added
