"""Monta a configuração de banco a partir de DATABASE_URL ou SQLite."""

from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


def config_banco(database_url: str | None, sqlite_path: Path) -> dict:
    """Devolve o dicionário de um banco Django.

    Sem URL, usa SQLite no caminho informado. Com URL, aceita
    ``postgres://`` ou ``postgresql://``. A senha pode vir escapada
    (``%40`` para ``@``). O parâmetro ``sslmode`` vira opção do psycopg.
    """
    if not database_url or not database_url.strip():
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }

    parsed = urlparse(database_url.strip())
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "DATABASE_URL deve começar com postgres:// ou postgresql://."
        )
    nome = unquote((parsed.path or "").lstrip("/"))
    if not nome:
        raise ValueError("DATABASE_URL precisa informar o nome do banco.")

    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": nome,
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
    }
    consulta = parse_qs(parsed.query)
    if "sslmode" in consulta and consulta["sslmode"]:
        config["OPTIONS"] = {"sslmode": consulta["sslmode"][0]}
    return config
