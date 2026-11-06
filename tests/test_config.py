import os
from pathlib import Path

import pytest

from config.database import config_banco
from config.env import carregar_env
from config.producao import (
    chave_secreta,
    debug_ligado,
    montar_allowed_hosts,
    montar_origens_csrf,
)


def test_sqlite_quando_nao_ha_url(tmp_path):
    config = config_banco(None, tmp_path / "db.sqlite3")
    assert config["ENGINE"] == "django.db.backends.sqlite3"
    assert config["NAME"] == tmp_path / "db.sqlite3"


def test_sqlite_quando_a_url_esta_vazia(tmp_path):
    config = config_banco("   ", tmp_path / "db.sqlite3")
    assert config["ENGINE"] == "django.db.backends.sqlite3"


def test_postgres_com_senha_escapada_e_ssl(tmp_path):
    config = config_banco(
        "postgresql://ana:segredo%40x@db.interno:5433/ozzy_gestao?sslmode=require",
        tmp_path / "ignorado",
    )
    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["NAME"] == "ozzy_gestao"
    assert config["USER"] == "ana"
    assert config["PASSWORD"] == "segredo@x"
    assert config["HOST"] == "db.interno"
    assert config["PORT"] == "5433"
    assert config["OPTIONS"]["sslmode"] == "require"


def test_esquema_que_nao_e_postgres_e_rejeitado(tmp_path):
    with pytest.raises(ValueError):
        config_banco("mysql://usuario:senha@localhost/ozzy", tmp_path / "x")


def test_carregar_env_nao_sobrescreve_o_ambiente(tmp_path, monkeypatch):
    arquivo = tmp_path / ".env"
    arquivo.write_text(
        'DJANGO_DEBUG=0\n# comentario\nsem-igual\nFOO="bar"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("DJANGO_DEBUG", "1")
    monkeypatch.delenv("FOO", raising=False)
    carregar_env(arquivo)
    assert os.environ["DJANGO_DEBUG"] == "1"
    assert os.environ["FOO"] == "bar"


def test_carregar_env_inexistente_nao_falha(tmp_path):
    carregar_env(tmp_path / "nao-existe.env")


def test_postgres_sem_nome_de_banco_e_rejeitado(tmp_path):
    with pytest.raises(ValueError):
        config_banco("postgres://ana:segredo@localhost", tmp_path / "x")


def test_debug_desliga_com_zero_e_no_render_sem_variavel():
    assert debug_ligado("0", em_render=False) is False
    assert debug_ligado("false", em_render=False) is False
    assert debug_ligado("nao", em_render=False) is False
    assert debug_ligado("1", em_render=True) is True
    assert debug_ligado(None, em_render=False) is True
    assert debug_ligado(None, em_render=True) is False


def test_hosts_incluem_onrender_e_o_hostname_da_plataforma():
    assert montar_allowed_hosts(None, None) == [
        "localhost",
        "127.0.0.1",
        ".onrender.com",
    ]
    assert montar_allowed_hosts(".onrender.com", "ozzy-gestao.onrender.com") == [
        ".onrender.com",
        "ozzy-gestao.onrender.com",
    ]


def test_csrf_acrescenta_a_url_publica_do_render():
    assert montar_origens_csrf("", "https://ozzy-gestao.onrender.com/") == [
        "https://ozzy-gestao.onrender.com",
    ]
    assert montar_origens_csrf(
        "https://ozzy.exemplo.com",
        "https://ozzy-gestao.onrender.com",
    ) == [
        "https://ozzy.exemplo.com",
        "https://ozzy-gestao.onrender.com",
    ]


def test_chave_secreta_prefere_django_secret_key():
    assert chave_secreta("da-disciplina", "outra") == "da-disciplina"
    assert chave_secreta(None, "outra") == "outra"
    assert chave_secreta("  ", "") == "dev-only-nao-usar-em-producao"
