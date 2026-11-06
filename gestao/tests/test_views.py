from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from gestao.models import FechamentoDia, Insumo, Pedido, Produto
from gestao.services import registrar_pedido

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario():
    return get_user_model().objects.create_user(username="ozzy", password="senha-teste")


@pytest.fixture
def logado(client, usuario):
    client.force_login(usuario)
    return client


def _html(resposta):
    return resposta.content.decode()


def test_saude_responde_sem_login(client):
    resposta = client.get(reverse("saude"))
    assert resposta.status_code == 200
    assert resposta.content == b"ok"


def test_paginas_do_app_exigem_login(client):
    for nome in ("novo_pedido", "fechamento", "estoque"):
        resposta = client.get(reverse(nome))
        assert resposta.status_code == 302
        assert "/entrar/" in resposta.url


def test_tela_de_login_e_csrf(client):
    html = _html(client.get(reverse("login")))
    assert "Entrar" in html
    assert "csrfmiddlewaretoken" in html


def test_login_rejeita_senha_errada_e_aceita_a_certa(client, usuario):
    errado = client.post(reverse("login"), {"username": "ozzy", "password": "nao-e-essa"})
    assert errado.status_code == 200
    assert "incorretos" in _html(errado)

    certo = client.post(reverse("login"), {"username": "ozzy", "password": "senha-teste"})
    assert certo.status_code == 302
    assert certo.url == reverse("novo_pedido")


def test_inicio_leva_ao_novo_pedido(logado):
    resposta = logado.get(reverse("inicio"))
    assert resposta.status_code == 302
    assert resposta.url == reverse("novo_pedido")


def test_sair_exige_post_e_encerra_a_sessao(logado):
    assert logado.get(reverse("logout")).status_code == 405
    saida = logado.post(reverse("logout"))
    assert saida.status_code == 302
    assert "/entrar/" in saida.url
    assert logado.get(reverse("estoque")).status_code == 302


def test_novo_pedido_lista_produto_ativo_e_o_botao(logado):
    Produto.objects.create(nome="Açaí 500 ml", preco=Decimal("18.00"))
    Produto.objects.create(nome="Açaí oculto", preco=Decimal("10.00"), ativo=False)
    html = _html(logado.get(reverse("novo_pedido")))
    assert "Açaí 500 ml" in html
    assert "Açaí oculto" not in html
    assert "Registrar pedido" in html
    assert "csrfmiddlewaretoken" in html
    assert "telefone" not in html.lower()
    assert "endereco" not in html.lower()
    assert "endereço" not in html.lower()


def test_registrar_pedido_grava_o_total_calculado(logado):
    acai = Produto.objects.create(nome="Açaí 500 ml", preco=Decimal("18.00"))
    granola = Produto.objects.create(nome="Adicional de granola", preco=Decimal("3.00"))
    resposta = logado.post(
        reverse("novo_pedido"),
        {
            "canal": "whatsapp",
            "cliente_nome": "Cliente Ana",
            "forma_pagamento": "pix",
            f"qtd_{acai.id}": 1,
            f"qtd_{granola.id}": 2,
        },
    )
    assert resposta.status_code == 302
    pedido = Pedido.objects.get()
    assert pedido.canal == "whatsapp"
    assert pedido.cliente_nome == "Cliente Ana"
    assert pedido.forma_pagamento == "pix"
    assert pedido.total == Decimal("24.00")
    assert pedido.itens.count() == 2
    pagina = _html(logado.get(resposta.url))
    assert "Pedido de Cliente Ana registrado. Total R$ 24,00." in pagina


def test_pedido_sem_item_ou_sem_nome_nao_grava(logado):
    acai = Produto.objects.create(nome="Açaí 300 ml", preco=Decimal("12.00"))
    sem_item = logado.post(
        reverse("novo_pedido"),
        {
            "canal": "ifood",
            "cliente_nome": "Cliente Bruno",
            "forma_pagamento": "cartao",
            f"qtd_{acai.id}": 0,
        },
    )
    assert sem_item.status_code == 200
    assert "pelo menos um produto" in _html(sem_item)
    sem_nome = logado.post(
        reverse("novo_pedido"),
        {
            "canal": "whatsapp",
            "cliente_nome": "   ",
            "forma_pagamento": "pix",
            f"qtd_{acai.id}": 1,
        },
    )
    assert sem_nome.status_code == 200
    assert "Informe o nome do cliente." in _html(sem_nome)
    assert Pedido.objects.count() == 0


def test_post_sem_csrf_e_recusado(usuario):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(usuario)
    acai = Produto.objects.create(nome="Açaí 300 ml", preco=Decimal("12.00"))
    resposta = cliente.post(
        reverse("novo_pedido"),
        {
            "canal": "whatsapp",
            "cliente_nome": "Cliente Ana",
            "forma_pagamento": "pix",
            f"qtd_{acai.id}": 1,
        },
    )
    assert resposta.status_code == 403
    assert Pedido.objects.count() == 0


def test_fechamento_mostra_canal_pagamento_e_ticket(logado):
    acai = Produto.objects.create(nome="Açaí 300 ml", preco=Decimal("10.00"))
    registrar_pedido(
        canal="ifood",
        cliente_nome="Cliente Bruno",
        forma_pagamento="cartao",
        itens=[(acai, 2)],
    )
    registrar_pedido(
        canal="whatsapp",
        cliente_nome="Cliente Ana",
        forma_pagamento="pix",
        itens=[(acai, 1)],
    )
    html = _html(logado.get(reverse("fechamento")))
    assert "R$ 30,00" in html
    assert "R$ 20,00" in html
    assert "R$ 10,00" in html
    assert "Ticket médio" in html
    assert "R$ 15,00" in html
    assert "Fechar o dia" in html
    assert "Cliente Ana" in html
    assert "Cliente Bruno" in html
    assert "Nenhum pedido registrado hoje." not in html


def test_fechar_o_dia_grava_divergencia_e_nao_repete(logado):
    acai = Produto.objects.create(nome="Açaí 300 ml", preco=Decimal("10.00"))
    registrar_pedido(
        canal="whatsapp",
        cliente_nome="Cliente Ana",
        forma_pagamento="dinheiro",
        itens=[(acai, 1)],
    )
    fechou = logado.post(reverse("fechamento"), {"valor_conferido": "8,50"})
    assert fechou.status_code == 302
    fechamento = FechamentoDia.objects.get()
    assert fechamento.data == timezone.localdate()
    assert fechamento.valor_conferido == Decimal("8.50")
    assert fechamento.total_geral == Decimal("10.00")
    assert fechamento.divergencia == Decimal("-1.50")

    pagina = _html(logado.get(reverse("fechamento")))
    assert "Dia fechado" in pagina
    assert "-R$ 1,50" in pagina
    assert "Fechar o dia" not in pagina

    de_novo = logado.post(reverse("fechamento"), {"valor_conferido": "10,00"})
    assert de_novo.status_code == 200
    assert "já foi fechado" in _html(de_novo)
    assert FechamentoDia.objects.count() == 1


def test_valor_conferido_invalido_nao_fecha(logado):
    resposta = logado.post(reverse("fechamento"), {"valor_conferido": "abc"})
    assert resposta.status_code == 200
    assert "86,50" in _html(resposta)
    assert FechamentoDia.objects.count() == 0


def test_estoque_avisa_e_movimenta(logado):
    baixo = Insumo.objects.create(
        nome="Granola",
        unidade="kg",
        quantidade_atual=Decimal("0.400"),
        estoque_minimo=Decimal("0.800"),
    )
    Insumo.objects.create(
        nome="Polpa de açaí",
        unidade="kg",
        quantidade_atual=Decimal("6.000"),
        estoque_minimo=Decimal("4.000"),
    )
    html = _html(logado.get(reverse("estoque")))
    assert "Granola" in html
    assert "Acabando" in html
    assert "1 insumo está acabando." in html
    assert "Entrada" in html
    assert "Saída" in html

    entrada = logado.post(
        reverse("estoque"),
        {"insumo_id": baixo.id, "tipo": "entrada", "quantidade": "2,5"},
        follow=True,
    )
    assert "Entrada registrada." in _html(entrada)
    baixo.refresh_from_db()
    assert baixo.quantidade_atual == Decimal("2.900")

    saida = logado.post(
        reverse("estoque"),
        {"insumo_id": baixo.id, "tipo": "saida", "quantidade": "1"},
    )
    assert saida.status_code == 302
    baixo.refresh_from_db()
    assert baixo.quantidade_atual == Decimal("1.900")

    bloqueio = logado.post(
        reverse("estoque"),
        {"insumo_id": baixo.id, "tipo": "saida", "quantidade": "50"},
        follow=True,
    )
    assert "suficiente" in _html(bloqueio)
    baixo.refresh_from_db()
    assert baixo.quantidade_atual == Decimal("1.900")


def test_seed_aparece_no_fechamento_e_no_estoque(client):
    call_command("seed_demo")
    assert client.login(username="ozzy", password="acai-demo-2026")
    fechamento = _html(client.get(reverse("fechamento")))
    assert "Cliente Ana" in fechamento
    assert "Cliente Bruno" in fechamento
    assert "Cliente Carla" in fechamento
    assert "Cliente Diego" in fechamento
    assert "R$ 86,50" in fechamento
    assert "R$ 46,50" in fechamento
    assert "R$ 40,00" in fechamento
    assert "R$ 21,63" in fechamento

    estoque = _html(client.get(reverse("estoque")))
    assert "Polpa de cupuaçu" in estoque
    assert "Acabando" in estoque
    assert "4 insumos estão acabando." in estoque
