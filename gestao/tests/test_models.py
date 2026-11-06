from decimal import Decimal

import pytest
from django.db import IntegrityError

from gestao.models import Insumo, ItemPedido, Pedido, Produto

pytestmark = pytest.mark.django_db


def test_insumo_no_minimo_esta_abaixo_do_minimo():
    no_limite = Insumo.objects.create(
        nome="Granola",
        unidade="kg",
        quantidade_atual=Decimal("0.800"),
        estoque_minimo=Decimal("0.800"),
    )
    acima = Insumo.objects.create(
        nome="Polpa de açaí",
        unidade="kg",
        quantidade_atual=Decimal("4.001"),
        estoque_minimo=Decimal("4.000"),
    )
    assert no_limite.abaixo_do_minimo is True
    assert acima.abaixo_do_minimo is False


def test_pedido_guarda_apenas_o_nome_do_cliente():
    campos = {campo.name for campo in Pedido._meta.get_fields()}
    assert "cliente_nome" in campos
    assert "telefone" not in campos
    assert "endereco" not in campos
    assert "address" not in campos


def test_rotulos_de_canal_e_pagamento():
    assert Pedido.Canal.IFOOD.label == "iFood"
    assert Pedido.Canal.WHATSAPP.label == "WhatsApp"
    assert Pedido.FormaPagamento.IFOOD_ONLINE.value == "ifood_online"
    assert Pedido.FormaPagamento.PIX.label == "Pix"


@pytest.mark.django_db(transaction=True)
def test_item_rejeita_quantidade_zero():
    produto = Produto.objects.create(nome="Açaí 300 ml", preco=Decimal("12.00"))
    pedido = Pedido.objects.create(
        canal=Pedido.Canal.WHATSAPP,
        cliente_nome="Cliente Ana",
        forma_pagamento=Pedido.FormaPagamento.PIX,
        total=Decimal("0.00"),
    )
    with pytest.raises(IntegrityError):
        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=0,
            subtotal=Decimal("0.00"),
        )
