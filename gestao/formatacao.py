"""Textos de tela em português, sem depender do template."""

from decimal import Decimal

MESES = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def reais(valor) -> str:
    """Formata um valor como moeda brasileira: R$ 1.234,56."""
    quantizado = Decimal(valor or 0).quantize(Decimal("0.01"))
    sinal = "-" if quantizado < 0 else ""
    inteiro, centavos = f"{abs(quantizado):.2f}".split(".")
    partes = []
    while inteiro:
        partes.append(inteiro[-3:])
        inteiro = inteiro[:-3]
    return f"{sinal}R$ {'.'.join(reversed(partes))},{centavos}"


def quantidade_br(valor) -> str:
    """Mostra a quantidade com vírgula e sem zeros à direita."""
    texto = format(Decimal(valor or 0), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def data_por_extenso(data) -> str:
    return f"{data.day} de {MESES[data.month - 1]} de {data.year}"
