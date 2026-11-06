"""Regras de negócio do registro de pedidos, do estoque e do fechamento."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from gestao.models import (
    FechamentoDia,
    Insumo,
    ItemPedido,
    MovimentacaoEstoque,
    Pedido,
    Produto,
)

CENTAVOS = Decimal("0.01")
MILESIMOS = Decimal("0.001")


class ErroNegocio(Exception):
    """Regra de negócio que a tela pode mostrar com as mesmas palavras."""


class PedidoSemItens(ErroNegocio):
    pass


class EstoqueInsuficiente(ErroNegocio):
    pass


class QuantidadeInvalida(ErroNegocio):
    pass


class DiaJaFechado(ErroNegocio):
    pass


class ValorConferidoInvalido(ErroNegocio):
    pass


@dataclass(frozen=True)
class Grupo:
    chave: str
    rotulo: str
    total: Decimal
    quantidade: int


@dataclass(frozen=True)
class ResumoDia:
    data: date
    total: Decimal
    quantidade: int
    ticket_medio: Decimal
    canais: tuple[Grupo, ...]
    pagamentos: tuple[Grupo, ...]
    pedidos: list[Pedido]


def decimal_de(valor) -> Decimal:
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def dinheiro(valor) -> Decimal:
    return decimal_de(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _normalizar_numero(texto: str) -> str:
    bruto = texto.strip()
    if "," in bruto and "." in bruto:
        return bruto.replace(".", "").replace(",", ".")
    return bruto.replace(",", ".")


def analisar_dinheiro(texto: str) -> Decimal:
    """Aceita 86,50, 86.50 ou 1.234,56 e devolve um valor com centavos."""
    bruto = (texto or "").strip()
    if not bruto:
        raise ValorConferidoInvalido("Informe o valor conferido em caixa.")
    try:
        valor = Decimal(_normalizar_numero(bruto))
    except InvalidOperation as exc:
        raise ValorConferidoInvalido("Use um valor como 86,50.") from exc
    if valor < 0:
        raise ValorConferidoInvalido("O valor conferido não pode ser negativo.")
    return dinheiro(valor)


def analisar_quantidade(texto: str) -> Decimal:
    """Aceita 1,5 ou 2 e devolve a quantidade com três casas decimais."""
    bruto = (texto or "").strip()
    if not bruto:
        raise QuantidadeInvalida("Informe a quantidade.")
    try:
        valor = Decimal(_normalizar_numero(bruto))
    except InvalidOperation as exc:
        raise QuantidadeInvalida("Use um número como 1,5.") from exc
    return valor.quantize(MILESIMOS, rounding=ROUND_HALF_UP)


def registrar_pedido(
    *,
    canal: str,
    cliente_nome: str,
    forma_pagamento: str,
    itens: list[tuple[Produto, int]],
) -> Pedido:
    """Grava o pedido e calcula o total a partir do preço atual de cada produto."""
    nome = " ".join((cliente_nome or "").split())
    if not nome:
        raise ErroNegocio("Informe o nome do cliente.")
    if len(nome) > 120:
        raise ErroNegocio("O nome do cliente está longo demais.")
    if canal not in Pedido.Canal.values:
        raise ErroNegocio("Escolha de onde veio o pedido.")
    if forma_pagamento not in Pedido.FormaPagamento.values:
        raise ErroNegocio("Escolha a forma de pagamento.")

    preparados: list[tuple[Produto, int, Decimal]] = []
    for produto, quantidade in itens:
        if quantidade is None or quantidade == 0:
            continue
        if quantidade < 0:
            raise QuantidadeInvalida("A quantidade não pode ser negativa.")
        if quantidade > 99:
            raise QuantidadeInvalida("A quantidade máxima por produto é 99.")
        if not produto.ativo:
            raise ErroNegocio(f"{produto.nome} não está no cardápio.")
        subtotal = dinheiro(produto.preco * quantidade)
        preparados.append((produto, quantidade, subtotal))

    if not preparados:
        raise PedidoSemItens("Escolha pelo menos um produto.")

    total = dinheiro(sum((subtotal for _, _, subtotal in preparados), Decimal("0")))
    with transaction.atomic():
        pedido = Pedido.objects.create(
            canal=canal,
            cliente_nome=nome,
            forma_pagamento=forma_pagamento,
            total=total,
        )
        ItemPedido.objects.bulk_create(
            [
                ItemPedido(
                    pedido=pedido,
                    produto=produto,
                    quantidade=quantidade,
                    subtotal=subtotal,
                )
                for produto, quantidade, subtotal in preparados
            ]
        )
    return pedido


def registrar_movimentacao(insumo: Insumo, tipo: str, quantidade) -> MovimentacaoEstoque:
    """Dá entrada ou saída e atualiza a quantidade atual do insumo."""
    if tipo not in MovimentacaoEstoque.Tipo.values:
        raise ErroNegocio("Escolha entrada ou saída.")
    qtd = decimal_de(quantidade).quantize(MILESIMOS, rounding=ROUND_HALF_UP)
    if qtd <= 0:
        raise QuantidadeInvalida("A quantidade precisa ser maior que zero.")

    with transaction.atomic():
        atual = Insumo.objects.get(pk=insumo.pk)
        if tipo == MovimentacaoEstoque.Tipo.SAIDA and atual.quantidade_atual < qtd:
            raise EstoqueInsuficiente(
                f"Não há {atual.nome} suficiente para essa saída."
            )
        if tipo == MovimentacaoEstoque.Tipo.SAIDA:
            novo_saldo = atual.quantidade_atual - qtd
        else:
            novo_saldo = atual.quantidade_atual + qtd
        atual.quantidade_atual = novo_saldo.quantize(MILESIMOS, rounding=ROUND_HALF_UP)
        atual.save(update_fields=["quantidade_atual"])
        movimento = MovimentacaoEstoque.objects.create(
            insumo=atual,
            tipo=tipo,
            quantidade=qtd,
        )
    insumo.quantidade_atual = atual.quantidade_atual
    return movimento


def _intervalo_do_dia(data: date) -> tuple[datetime, datetime]:
    fuso = timezone.get_current_timezone()
    inicio = timezone.make_aware(datetime.combine(data, time.min), fuso)
    return inicio, inicio + timedelta(days=1)


def pedidos_no_dia(data: date):
    inicio, fim = _intervalo_do_dia(data)
    return (
        Pedido.objects.filter(created_at__gte=inicio, created_at__lt=fim)
        .prefetch_related("itens__produto")
        .order_by("created_at")
    )


def _grupos(qs, campo: str, escolhas) -> tuple[Grupo, ...]:
    totais = {chave: dinheiro(0) for chave, _rotulo in escolhas}
    quantidades = {chave: 0 for chave, _rotulo in escolhas}
    # order_by() limpa a ordenação do model; senão o Django agrupa por created_at.
    consulta = qs.order_by().values(campo).annotate(soma=Sum("total"), qtd=Count("id"))
    for linha in consulta:
        chave = linha[campo]
        if chave not in totais:
            continue
        totais[chave] = dinheiro(linha["soma"] or 0)
        quantidades[chave] = linha["qtd"]
    return tuple(
        Grupo(chave, rotulo, totais[chave], quantidades[chave])
        for chave, rotulo in escolhas
    )


def resumo_do_dia(data: date | None = None) -> ResumoDia:
    """Soma os pedidos da data (fuso de João Pessoa) por canal e pagamento."""
    if data is None:
        data = timezone.localdate()
    qs = pedidos_no_dia(data)
    agregado = qs.aggregate(total=Sum("total"), quantidade=Count("id"))
    total = dinheiro(agregado["total"] or 0)
    quantidade = agregado["quantidade"] or 0
    ticket = dinheiro(total / quantidade) if quantidade else dinheiro(0)
    return ResumoDia(
        data=data,
        total=total,
        quantidade=quantidade,
        ticket_medio=ticket,
        canais=_grupos(qs, "canal", Pedido.Canal.choices),
        pagamentos=_grupos(qs, "forma_pagamento", Pedido.FormaPagamento.choices),
        pedidos=list(qs),
    )


def fechar_dia(data: date, valor_conferido) -> FechamentoDia:
    """Grava o fechamento. A divergência não muda se entrarem pedidos depois."""
    if FechamentoDia.objects.filter(data=data).exists():
        raise DiaJaFechado("Este dia já foi fechado.")
    valor = dinheiro(valor_conferido)
    if valor < 0:
        raise ValorConferidoInvalido("O valor conferido não pode ser negativo.")
    resumo = resumo_do_dia(data)
    canais = {grupo.chave: grupo.total for grupo in resumo.canais}
    pagamentos = {grupo.chave: grupo.total for grupo in resumo.pagamentos}
    return FechamentoDia.objects.create(
        data=data,
        valor_conferido=valor,
        total_geral=resumo.total,
        total_ifood=canais[Pedido.Canal.IFOOD],
        total_whatsapp=canais[Pedido.Canal.WHATSAPP],
        total_pix=pagamentos[Pedido.FormaPagamento.PIX],
        total_dinheiro=pagamentos[Pedido.FormaPagamento.DINHEIRO],
        total_cartao=pagamentos[Pedido.FormaPagamento.CARTAO],
        total_ifood_online=pagamentos[Pedido.FormaPagamento.IFOOD_ONLINE],
        quantidade_pedidos=resumo.quantidade,
        ticket_medio=resumo.ticket_medio,
        divergencia=dinheiro(valor - resumo.total),
    )
