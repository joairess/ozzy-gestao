from django.contrib import admin

from gestao.models import (
    FechamentoDia,
    Insumo,
    ItemPedido,
    MovimentacaoEstoque,
    Pedido,
    Produto,
)


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("created_at", "canal", "cliente_nome", "forma_pagamento", "total")
    list_filter = ("canal", "forma_pagamento")
    search_fields = ("cliente_nome",)
    readonly_fields = ("created_at",)
    inlines = [ItemPedidoInline]


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ("nome", "unidade", "quantidade_atual", "estoque_minimo")
    search_fields = ("nome",)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("created_at", "insumo", "tipo", "quantidade")
    list_filter = ("tipo",)
    readonly_fields = ("created_at",)


@admin.register(FechamentoDia)
class FechamentoDiaAdmin(admin.ModelAdmin):
    list_display = ("data", "total_geral", "valor_conferido", "divergencia", "fechado_em")
    readonly_fields = ("fechado_em",)
