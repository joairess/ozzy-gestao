from pathlib import Path


def _luminancia(hex_cor: str) -> float:
    canal = hex_cor.lstrip("#")
    vermelho, verde, azul = (int(canal[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def linear(componente: float) -> float:
        if componente <= 0.04045:
            return componente / 12.92
        return ((componente + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(vermelho) + 0.7152 * linear(verde) + 0.0722 * linear(azul)


def contraste(frente: str, fundo: str) -> float:
    claro, escuro = sorted((_luminancia(frente), _luminancia(fundo)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def test_cores_da_interface_passam_no_contraste_aa():
    css = Path("gestao/static/gestao/app.css").read_text(encoding="utf-8").upper()
    pares = [
        ("#1C1226", "#FFF8F4", 4.5),
        ("#FFFFFF", "#3C145C", 4.5),
        ("#3C145C", "#FFFFFF", 4.5),
        ("#6E1220", "#FDECEC", 4.5),
        ("#14532D", "#E7F6EC", 4.5),
        ("#FFFFFF", "#6E1220", 4.5),
        ("#FFFFFF", "#14532D", 4.5),
        ("#5C4A3E", "#FFFFFF", 3),
        ("#1C1226", "#FFFFFF", 4.5),
    ]
    for frente, fundo, minimo in pares:
        assert frente.upper() in css
        assert fundo.upper() in css
        assert contraste(frente, fundo) >= minimo


def test_css_usa_fonte_grande_e_botao_alto():
    css = Path("gestao/static/gestao/app.css").read_text(encoding="utf-8")
    assert "font-size: 1.125rem" in css
    assert "min-height: 3.25rem" in css
    assert "font-size:" not in css.replace("font-size: 1.125rem", "").replace(
        "font-size: 1.25rem", ""
    ).replace("font-size: 1.35rem", "").replace("font-size: 1.5rem", "").replace(
        "font-size: 1.75rem", ""
    ).replace("font-size: 2rem", "")


def test_bootstrap_5_esta_no_projeto():
    css = Path("gestao/static/gestao/vendor/bootstrap.min.css").read_text(encoding="utf-8")
    assert "Bootstrap  v5.3.3" in css
