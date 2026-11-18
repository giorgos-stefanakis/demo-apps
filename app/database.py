import psycopg
from psycopg.rows import dict_row

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id          bigserial PRIMARY KEY,
    object_key  text UNIQUE NOT NULL,
    filename    text NOT NULL,
    size_bytes  bigint NOT NULL,
    sha256      text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
)
"""


def ensure_schema(database_url: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(SCHEMA)


def insert_file(database_url: str, object_key: str, filename: str, size_bytes: int, sha256: str) -> None:
    with psycopg.connect(database_url) as connection:
        connection.execute(
            "INSERT INTO files (object_key, filename, size_bytes, sha256) VALUES (%s, %s, %s, %s)"
            " ON CONFLICT (object_key) DO NOTHING",
            (object_key, filename, size_bytes, sha256),
        )


def list_files(database_url: str) -> list[dict]:
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        return connection.execute(
            "SELECT object_key, filename, size_bytes, sha256, created_at FROM files ORDER BY created_at DESC"
        ).fetchall()
