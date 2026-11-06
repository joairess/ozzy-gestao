"""Monta a configuração de banco a partir de DATABASE_URL ou SQLite."""

from pathlib import Path
from urllib.parse import urlparse

import dj_database_url


def config_banco(database_url: str | None, sqlite_path: Path) -> dict:
    """Devolve o dicionário de um banco Django.

    Sem URL, usa SQLite no caminho informado. Com URL, aceita
    ``postgres://`` ou ``postgresql://`` pelo pacote dj-database-url. A
    senha pode vir escapada (``%40`` para ``@``). O parâmetro ``sslmode``
    vira opção do psycopg.
    """
    if not database_url or not database_url.strip():
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }

    url = database_url.strip()
    if urlparse(url).scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "DATABASE_URL deve começar com postgres:// ou postgresql://."
        )

    config = dj_database_url.parse(url)
    if not config.get("NAME"):
        raise ValueError("DATABASE_URL precisa informar o nome do banco.")
    if config.get("PORT") not in (None, ""):
        config["PORT"] = str(config["PORT"])
    return config
