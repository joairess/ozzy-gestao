from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from gestao.models import Insumo, Pedido, Produto

pytestmark = pytest.mark.django_db


def test_seed_e_idempotente_e_traz_alerta_de_estoque():
    call_command("seed_demo")
    call_command("seed_demo")

    usuario = get_user_model().objects.get(username="ozzy")
    assert usuario.check_password("acai-demo-2026")
    assert usuario.is_superuser is True
    assert Produto.objects.filter(nome="Açaí 500 ml").count() == 1
    assert Pedido.objects.filter(cliente_nome="Cliente Ana").count() == 1

    pedido = Pedido.objects.get(cliente_nome="Cliente Ana")
    assert pedido.total == Decimal("21.00")
    assert pedido.canal == "whatsapp"
    assert list(pedido.itens.order_by("produto__nome").values_list("quantidade", flat=True)) == [1, 1]

    polpa = Insumo.objects.get(nome="Polpa de açaí")
    assert polpa.quantidade_atual == Decimal("6.000")
    assert polpa.movimentacoes.count() == 2

    cupuacu = Insumo.objects.get(nome="Polpa de cupuaçu")
    assert cupuacu.abaixo_do_minimo is True

    nomes = set(Pedido.objects.values_list("cliente_nome", flat=True))
    assert nomes == {"Cliente Ana", "Cliente Bruno", "Cliente Carla", "Cliente Diego"}
    hoje = timezone.localdate()
    for pedido_demo in Pedido.objects.all():
        assert timezone.localtime(pedido_demo.created_at).date() == hoje
