"""Modelos do Ozzy Gestão.

O pedido guarda só o nome do cliente — sem telefone e sem endereço —
para reduzir o dado pessoal tratado (LGPD). O fechamento do dia é um
registro calculado a partir dos pedidos da data.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Produto(models.Model):
    nome = models.CharField("nome", max_length=120)
    preco = models.DecimalField(
        "preço",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(preco__gte=0),
                name="produto_preco_nao_negativo",
            )
        ]

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    class Canal(models.TextChoices):
        IFOOD = "ifood", "iFood"
        WHATSAPP = "whatsapp", "WhatsApp"

    class FormaPagamento(models.TextChoices):
        PIX = "pix", "Pix"
        DINHEIRO = "dinheiro", "Dinheiro"
        CARTAO = "cartao", "Cartão"
        IFOOD_ONLINE = "ifood_online", "Pago no iFood"

    canal = models.CharField("canal", max_length=20, choices=Canal.choices)
    cliente_nome = models.CharField("nome do cliente", max_length=120)
    forma_pagamento = models.CharField(
        "forma de pagamento",
        max_length=20,
        choices=FormaPagamento.choices,
    )
    total = models.DecimalField("total", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("registrado em", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="pedido_total_nao_negativo",
            )
        ]

    def __str__(self):
        return f"{self.cliente_nome} — {self.get_canal_display()}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="pedido",
    )
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="itens",
        verbose_name="produto",
    )
    quantidade = models.PositiveIntegerField("quantidade")
    subtotal = models.DecimalField("subtotal", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantidade__gte=1),
                name="item_quantidade_minima",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0),
                name="item_subtotal_nao_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.quantidade}× {self.produto}"


class Insumo(models.Model):
    nome = models.CharField("nome", max_length=120, unique=True)
    unidade = models.CharField("unidade", max_length=20)
    quantidade_atual = models.DecimalField(
        "quantidade atual",
        max_digits=10,
        decimal_places=3,
    )
    estoque_minimo = models.DecimalField(
        "estoque mínimo",
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        ordering = ["nome"]
        verbose_name = "insumo"
        verbose_name_plural = "insumos"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantidade_atual__gte=0),
                name="insumo_quantidade_nao_negativa",
            ),
            models.CheckConstraint(
                condition=models.Q(estoque_minimo__gte=0),
                name="insumo_minimo_nao_negativo",
            ),
        ]

    def __str__(self):
        return self.nome

    @property
    def abaixo_do_minimo(self) -> bool:
        """Verdadeiro quando a quantidade atual chegou no mínimo ou passou dele."""
        return self.quantidade_atual <= self.estoque_minimo


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SAIDA = "saida", "Saída"

    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.PROTECT,
        related_name="movimentacoes",
        verbose_name="insumo",
    )
    tipo = models.CharField("tipo", max_length=10, choices=Tipo.choices)
    quantidade = models.DecimalField("quantidade", max_digits=10, decimal_places=3)
    created_at = models.DateTimeField("registrada em", auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "movimentação de estoque"
        verbose_name_plural = "movimentações de estoque"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0),
                name="movimento_quantidade_positiva",
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.quantidade} {self.insumo.unidade} em {self.insumo}"


class FechamentoDia(models.Model):
    """Fotografia do caixa no momento em que o dia foi fechado.

    A divergência é o valor conferido em caixa menos o total dos pedidos.
    Número negativo significa que entrou menos do que o sistema registrou.
    """

    data = models.DateField("data", unique=True)
    valor_conferido = models.DecimalField(
        "valor conferido em caixa",
        max_digits=10,
        decimal_places=2,
    )
    total_geral = models.DecimalField("total do dia", max_digits=10, decimal_places=2)
    total_ifood = models.DecimalField("total iFood", max_digits=10, decimal_places=2)
    total_whatsapp = models.DecimalField("total WhatsApp", max_digits=10, decimal_places=2)
    total_pix = models.DecimalField("total Pix", max_digits=10, decimal_places=2)
    total_dinheiro = models.DecimalField("total dinheiro", max_digits=10, decimal_places=2)
    total_cartao = models.DecimalField("total cartão", max_digits=10, decimal_places=2)
    total_ifood_online = models.DecimalField(
        "total pago no iFood",
        max_digits=10,
        decimal_places=2,
    )
    quantidade_pedidos = models.PositiveIntegerField("quantidade de pedidos")
    ticket_medio = models.DecimalField("ticket médio", max_digits=10, decimal_places=2)
    divergencia = models.DecimalField("divergência", max_digits=10, decimal_places=2)
    fechado_em = models.DateTimeField("fechado em", auto_now_add=True)

    class Meta:
        ordering = ["-data"]
        verbose_name = "fechamento do dia"
        verbose_name_plural = "fechamentos do dia"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor_conferido__gte=0),
                name="fechamento_valor_conferido_nao_negativo",
            )
        ]

    def __str__(self):
        return f"Fechamento {self.data:%d/%m/%Y}"
