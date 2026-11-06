from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.hashers import identify_hasher
from django.utils import timezone

from gestao.models import Insumo, MovimentacaoEstoque, Pedido, Produto
from gestao.services import (
    DiaJaFechado,
    ErroNegocio,
    EstoqueInsuficiente,
    PedidoSemItens,
    QuantidadeInvalida,
    ValorConferidoInvalido,
    analisar_dinheiro,
    analisar_quantidade,
    fechar_dia,
    registrar_movimentacao,
    registrar_pedido,
    resumo_do_dia,
)

pytestmark = pytest.mark.django_db


def _produto(nome="Açaí 500 ml", preco="18.00", ativo=True):
    return Produto.objects.create(nome=nome, preco=Decimal(preco), ativo=ativo)


def test_registrar_pedido_calcula_subtotal_e_ignora_quantidade_zero():
    acai = _produto()
    granola = _produto("Adicional de granola", "3.00")
    pedido = registrar_pedido(
        canal="whatsapp",
        cliente_nome="  Cliente   Ana ",
        forma_pagamento="pix",
        itens=[(acai, 2), (granola, 0), (granola, 1)],
    )
    assert pedido.cliente_nome == "Cliente Ana"
    assert pedido.total == Decimal("39.00")
    assert pedido.itens.count() == 2
    item = pedido.itens.get(produto=acai)
    assert item.quantidade == 2
    assert item.subtotal == Decimal("36.00")


def test_pedido_sem_itens_nao_e_gravado():
    acai = _produto()
    with pytest.raises(PedidoSemItens):
        registrar_pedido(
            canal="ifood",
            cliente_nome="Cliente Bruno",
            forma_pagamento="cartao",
            itens=[(acai, 0)],
        )
    assert Pedido.objects.count() == 0


def test_produto_inativo_nao_entra_no_pedido():
    acai = _produto(ativo=False)
    with pytest.raises(ErroNegocio):
        registrar_pedido(
            canal="whatsapp",
            cliente_nome="Cliente Ana",
            forma_pagamento="dinheiro",
            itens=[(acai, 1)],
        )


def test_quantidade_acima_do_limite():
    acai = _produto()
    with pytest.raises(QuantidadeInvalida):
        registrar_pedido(
            canal="whatsapp",
            cliente_nome="Cliente Ana",
            forma_pagamento="pix",
            itens=[(acai, 100)],
        )


def test_saida_baixa_o_estoque_e_bloqueia_saldo_negativo():
    insumo = Insumo.objects.create(
        nome="Granola",
        unidade="kg",
        quantidade_atual=Decimal("1.000"),
        estoque_minimo=Decimal("0.500"),
    )
    registrar_movimentacao(insumo, MovimentacaoEstoque.Tipo.SAIDA, Decimal("0.250"))
    insumo.refresh_from_db()
    assert insumo.quantidade_atual == Decimal("0.750")
    assert insumo.abaixo_do_minimo is False

    registrar_movimentacao(insumo, "saida", Decimal("0.300"))
    insumo.refresh_from_db()
    assert insumo.quantidade_atual == Decimal("0.450")
    assert insumo.abaixo_do_minimo is True

    with pytest.raises(EstoqueInsuficiente):
        registrar_movimentacao(insumo, "saida", Decimal("10"))
    insumo.refresh_from_db()
    assert insumo.quantidade_atual == Decimal("0.450")
    assert MovimentacaoEstoque.objects.count() == 2


def test_entrada_soma_a_quantidade():
    insumo = Insumo.objects.create(
        nome="Copo 500 ml",
        unidade="un",
        quantidade_atual=Decimal("25"),
        estoque_minimo=Decimal("40"),
    )
    registrar_movimentacao(insumo, "entrada", "15")
    insumo.refresh_from_db()
    assert insumo.quantidade_atual == Decimal("40.000")
    assert insumo.abaixo_do_minimo is True


def test_resumo_separa_canal_pagamento_e_ignora_outro_dia():
    acai = _produto("Açaí 300 ml", "10.00")
    vitamina = _produto("Vitamina de cupuaçu", "5.00")
    registrar_pedido(
        canal="whatsapp",
        cliente_nome="Cliente Ana",
        forma_pagamento="pix",
        itens=[(acai, 1)],
    )
    registrar_pedido(
        canal="ifood",
        cliente_nome="Cliente Bruno",
        forma_pagamento="ifood_online",
        itens=[(acai, 1)],
    )
    terceiro = registrar_pedido(
        canal="ifood",
        cliente_nome="Cliente Carla",
        forma_pagamento="cartao",
        itens=[(vitamina, 1)],
    )
    antigo = registrar_pedido(
        canal="whatsapp",
        cliente_nome="Cliente Diego",
        forma_pagamento="dinheiro",
        itens=[(acai, 1)],
    )
    antigo.created_at = timezone.now() - timedelta(days=1)
    antigo.save(update_fields=["created_at"])

    resumo = resumo_do_dia(timezone.localdate())
    assert resumo.quantidade == 3
    assert resumo.total == Decimal("25.00")
    assert resumo.ticket_medio == Decimal("8.33")
    canais = {grupo.chave: grupo for grupo in resumo.canais}
    pagamentos = {grupo.chave: grupo for grupo in resumo.pagamentos}
    assert canais["whatsapp"].total == Decimal("10.00")
    assert canais["whatsapp"].quantidade == 1
    assert canais["ifood"].total == Decimal("15.00")
    assert pagamentos["pix"].total == Decimal("10.00")
    assert pagamentos["ifood_online"].total == Decimal("10.00")
    assert pagamentos["cartao"].total == Decimal("5.00")
    assert pagamentos["dinheiro"].total == Decimal("0.00")
    assert terceiro.cliente_nome in {pedido.cliente_nome for pedido in resumo.pedidos}
    assert "Cliente Diego" not in {pedido.cliente_nome for pedido in resumo.pedidos}


def test_fechar_dia_grava_divergencia_e_nao_repete():
    acai = _produto("Açaí 300 ml", "10.00")
    registrar_pedido(
        canal="whatsapp",
        cliente_nome="Cliente Ana",
        forma_pagamento="dinheiro",
        itens=[(acai, 3)],
    )
    hoje = timezone.localdate()
    fechamento = fechar_dia(hoje, Decimal("25.00"))
    assert fechamento.total_geral == Decimal("30.00")
    assert fechamento.total_whatsapp == Decimal("30.00")
    assert fechamento.total_ifood == Decimal("0.00")
    assert fechamento.total_dinheiro == Decimal("30.00")
    assert fechamento.quantidade_pedidos == 1
    assert fechamento.ticket_medio == Decimal("30.00")
    assert fechamento.divergencia == Decimal("-5.00")
    assert fechamento.valor_conferido == Decimal("25.00")

    with pytest.raises(DiaJaFechado):
        fechar_dia(hoje, Decimal("30.00"))


def test_analisar_dinheiro_aceita_formato_brasileiro():
    assert analisar_dinheiro("1.234,56") == Decimal("1234.56")
    assert analisar_dinheiro("86.50") == Decimal("86.50")
    with pytest.raises(ValorConferidoInvalido):
        analisar_dinheiro("-1")
    with pytest.raises(ValorConferidoInvalido):
        analisar_dinheiro("abc")


def test_analisar_quantidade_aceita_virgula():
    assert analisar_quantidade("1,5") == Decimal("1.500")
    with pytest.raises(QuantidadeInvalida):
        analisar_quantidade("")


def test_senha_de_usuario_fica_com_hash():
    from django.contrib.auth import get_user_model

    usuario = get_user_model().objects.create_user("ozzy", password="senha-teste")
    assert usuario.password != "senha-teste"
    assert identify_hasher(usuario.password).algorithm.startswith("pbkdf2")
