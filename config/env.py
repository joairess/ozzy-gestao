"""Leitura simples de um arquivo .env, sem dependência extra."""

import os
from pathlib import Path


def carregar_env(caminho: Path) -> None:
    """Define variáveis que ainda não existem no ambiente.

    Linhas em branco e comentários (#) são ignoradas. Valores já presentes
    no ambiente — por exemplo, no GitHub Actions — não são sobrescritos.
    """
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and chave not in os.environ:
            os.environ[chave] = valor
