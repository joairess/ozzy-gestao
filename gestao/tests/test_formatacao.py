from datetime import date
from decimal import Decimal

from gestao.formatacao import data_por_extenso, quantidade_br, reais


def test_reais_com_milhar_e_negativo():
    assert reais(Decimal("1234.56")) == "R$ 1.234,56"
    assert reais(Decimal("-1.5")) == "-R$ 1,50"
    assert reais(Decimal("0")) == "R$ 0,00"
    assert reais(Decimal("86.50")) == "R$ 86,50"


def test_quantidade_br_tira_zeros():
    assert quantidade_br(Decimal("1.200")) == "1,2"
    assert quantidade_br(Decimal("0.400")) == "0,4"
    assert quantidade_br(Decimal("80")) == "80"


def test_data_por_extenso():
    assert data_por_extenso(date(2026, 11, 6)) == "6 de novembro de 2026"
