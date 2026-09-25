"""PostgreSQL connection and schema setup. Credentials never enter logs."""

from pathlib import Path

import psycopg
from psycopg.rows import dict_row


ROOT = Path(__file__).resolve().parents[1]


def local_settings() -> dict[str, str]:
    """Read only the four PostgreSQL settings from the existing Compose file."""
    result = {}
    for line in (ROOT / "compose" / ".env").read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT"}:
            result[key] = value.strip().strip('"').strip("'")
    missing = {"POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_PORT"} - result.keys()
    if missing:
        raise ValueError("Missing PostgreSQL configuration")
    return result


def connect():
    settings = local_settings()
    return psycopg.connect(
        host="127.0.0.1",
        port=int(settings["POSTGRES_PORT"]),
        dbname=settings["POSTGRES_DB"],
        user=settings["POSTGRES_USER"],
        password=settings["POSTGRES_PASSWORD"],
        connect_timeout=3,
        row_factory=dict_row,
    )


def initialize() -> None:
    with connect() as connection:
        connection.execute((ROOT / "database" / "001_first_slice.sql").read_text(encoding="utf-8"))
