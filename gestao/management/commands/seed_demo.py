"""Dados fictícios para demonstrar o Ozzy Gestão."""

import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from gestao.models import Insumo, Pedido, Produto
from gestao.services import registrar_movimentacao, registrar_pedido

SENHA_PADRAO = "acai-demo-2026"


class Command(BaseCommand):
    help = "Cria um usuário de demonstração, o cardápio, insumos e pedidos fictícios."

    def handle(self, *args, **options):
        self._usuario()
        produtos = self._produtos()
        self._insumos()
        self._pedidos(produtos)
        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write("Usuário: ozzy")
        self.stdout.write(
            "A senha é a variável DEMO_PASSWORD ou o valor documentado no README. "
            "Se o usuário já existia, a senha não foi alterada."
        )

    def _usuario(self):
        User = get_user_model()
        usuario, criado = User.objects.get_or_create(
            username="ozzy",
            defaults={
                "email": "ozzy@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if criado:
            usuario.set_password(os.environ.get("DEMO_PASSWORD", SENHA_PADRAO))
            usuario.save(update_fields=["password"])

    def _produtos(self):
        catalogo = [
            ("Açaí 300 ml", Decimal("12.00")),
            ("Açaí 500 ml", Decimal("18.00")),
            ("Açaí 700 ml", Decimal("22.00")),
            ("Vitamina de cupuaçu", Decimal("16.00")),
            ("Adicional de granola", Decimal("3.00")),
            ("Adicional de leite em pó", Decimal("3.50")),
        ]
        produtos = {}
        for nome, preco in catalogo:
            produto, _criado = Produto.objects.get_or_create(
                nome=nome,
                defaults={"preco": preco, "ativo": True},
            )
            produtos[nome] = produto
        return produtos

    def _insumos(self):
        # Quantidade inicial, mínimo e, se houver, movimentos aplicados só na criação.
        catalogo = [
            ("Polpa de açaí", "kg", Decimal("5.000"), Decimal("4.000"), [("entrada", Decimal("2")), ("saida", Decimal("1"))]),
            ("Polpa de cupuaçu", "kg", Decimal("1.200"), Decimal("2.000"), []),
            ("Granola", "kg", Decimal("0.400"), Decimal("0.800"), []),
            ("Leite em pó", "kg", Decimal("1.500"), Decimal("0.500"), []),
            ("Copo 300 ml", "un", Decimal("80"), Decimal("40"), []),
            ("Copo 500 ml", "un", Decimal("25"), Decimal("40"), []),
            ("Copo 700 ml", "un", Decimal("60"), Decimal("30"), []),
            ("Tampa para copo", "un", Decimal("90"), Decimal("50"), []),
            ("Colher descartável", "un", Decimal("18"), Decimal("40"), []),
        ]
        for nome, unidade, atual, minimo, movimentos in catalogo:
            insumo, criado = Insumo.objects.get_or_create(
                nome=nome,
                defaults={
                    "unidade": unidade,
                    "quantidade_atual": atual,
                    "estoque_minimo": minimo,
                },
            )
            if not criado:
                continue
            for tipo, quantidade in movimentos:
                registrar_movimentacao(insumo, tipo, quantidade)

    def _pedidos(self, produtos):
        if Pedido.objects.exists():
            return
        exemplos = [
            (
                80,
                {
                    "canal": Pedido.Canal.WHATSAPP,
                    "cliente_nome": "Cliente Ana",
                    "forma_pagamento": Pedido.FormaPagamento.PIX,
                    "itens": [
                        (produtos["Açaí 500 ml"], 1),
                        (produtos["Adicional de granola"], 1),
                    ],
                },
            ),
            (
                50,
                {
                    "canal": Pedido.Canal.IFOOD,
                    "cliente_nome": "Cliente Bruno",
                    "forma_pagamento": Pedido.FormaPagamento.IFOOD_ONLINE,
                    "itens": [(produtos["Açaí 300 ml"], 2)],
                },
            ),
            (
                35,
                {
                    "canal": Pedido.Canal.WHATSAPP,
                    "cliente_nome": "Cliente Carla",
                    "forma_pagamento": Pedido.FormaPagamento.DINHEIRO,
                    "itens": [
                        (produtos["Açaí 700 ml"], 1),
                        (produtos["Adicional de leite em pó"], 1),
                    ],
                },
            ),
            (
                15,
                {
                    "canal": Pedido.Canal.IFOOD,
                    "cliente_nome": "Cliente Diego",
                    "forma_pagamento": Pedido.FormaPagamento.CARTAO,
                    "itens": [(produtos["Vitamina de cupuaçu"], 1)],
                },
            ),
        ]
        agora = timezone.now()
        for minutos, dados in exemplos:
            pedido = registrar_pedido(**dados)
            pedido.created_at = agora - timedelta(minutes=minutos)
            pedido.save(update_fields=["created_at"])
