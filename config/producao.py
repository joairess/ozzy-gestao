"""Leitura das opções de produção a partir do ambiente."""

VALORES_DEBUG_LIGADO = {"1", "true", "sim", "yes", "on"}
HOSTS_PADRAO = "localhost,127.0.0.1,.onrender.com"
CHAVE_SECRETA_DEV = "dev-only-nao-usar-em-producao"


def debug_ligado(valor: str | None, em_render: bool) -> bool:
    """Liga o debug só no desenvolvimento local.

    ``DJANGO_DEBUG`` com 0, false, não ou valor vazio desliga o debug.
    Sem a variável, o debug fica desligado no Render e ligado fora dele.
    """
    if valor is None:
        return not em_render
    return valor.strip().lower() in VALORES_DEBUG_LIGADO


def montar_allowed_hosts(valor: str | None, hostname_render: str | None) -> list[str]:
    """Monta ALLOWED_HOSTS, incluindo o host .onrender.com por padrão."""
    bruto = HOSTS_PADRAO if valor is None else valor
    hosts = [parte.strip() for parte in bruto.split(",") if parte.strip()]
    hostname = (hostname_render or "").strip()
    if hostname and hostname not in hosts:
        hosts.append(hostname)
    return hosts


def montar_origens_csrf(valor: str | None, url_render: str | None) -> list[str]:
    """Monta CSRF_TRUSTED_ORIGINS e acrescenta a URL pública do Render."""
    origens = [parte.strip() for parte in (valor or "").split(",") if parte.strip()]
    url = (url_render or "").strip().rstrip("/")
    if url and url not in origens:
        origens.append(url)
    return origens


def chave_secreta(django_secret: str | None, secret_key: str | None) -> str:
    """Prefere DJANGO_SECRET_KEY e aceita SECRET_KEY como alternativa."""
    for valor in (django_secret, secret_key):
        if valor and valor.strip():
            return valor.strip()
    return CHAVE_SECRETA_DEV
