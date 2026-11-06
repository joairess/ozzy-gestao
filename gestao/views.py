"""Telas do balcão: novo pedido, fechamento do dia e estoque."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from gestao.formatacao import data_por_extenso, reais
from gestao.forms import formulario_pedido
from gestao.models import FechamentoDia, Insumo, MovimentacaoEstoque, Produto
from gestao.services import (
    ErroNegocio,
    Grupo,
    analisar_dinheiro,
    analisar_quantidade,
    fechar_dia,
    registrar_movimentacao,
    registrar_pedido,
    resumo_do_dia,
)


class NovoPedidoView(LoginRequiredMixin, FormView):
    template_name = "gestao/novo_pedido.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.produtos = list(Produto.objects.filter(ativo=True))
        else:
            self.produtos = []
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        dados = self.request.POST if self.request.method == "POST" else None
        return formulario_pedido(self.produtos, dados)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        formulario = contexto["form"]
        contexto["linhas"] = [
            {"produto": produto, "campo": formulario[f"qtd_{produto.id}"]}
            for produto in self.produtos
        ]
        return contexto

    def form_valid(self, form):
        itens = [
            (produto, form.cleaned_data.get(f"qtd_{produto.id}") or 0)
            for produto in self.produtos
        ]
        try:
            pedido = registrar_pedido(
                canal=form.cleaned_data["canal"],
                cliente_nome=form.cleaned_data["cliente_nome"],
                forma_pagamento=form.cleaned_data["forma_pagamento"],
                itens=itens,
            )
        except ErroNegocio as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Pedido de {pedido.cliente_nome} registrado. Total {reais(pedido.total)}.",
        )
        return redirect("novo_pedido")


class FechamentoView(LoginRequiredMixin, TemplateView):
    template_name = "gestao/fechamento.html"

    def get_context_data(self, **kwargs):
        hoje = timezone.localdate()
        resumo = resumo_do_dia(hoje)
        fechamento = FechamentoDia.objects.filter(data=hoje).first()
        contexto = super().get_context_data(**kwargs)
        contexto.update(
            {
                "resumo": resumo,
                "fechamento": fechamento,
                "data_extenso": data_por_extenso(hoje),
                "painel": _painel(resumo, fechamento),
                "pedidos_depois": bool(
                    fechamento
                    and (
                        fechamento.total_geral != resumo.total
                        or fechamento.quantidade_pedidos != resumo.quantidade
                    )
                ),
            }
        )
        return contexto

    def post(self, request, *args, **kwargs):
        try:
            valor = analisar_dinheiro(request.POST.get("valor_conferido", ""))
            fechar_dia(timezone.localdate(), valor)
        except ErroNegocio as exc:
            messages.error(request, str(exc))
            return self.get(request, *args, **kwargs)
        messages.success(request, "Dia fechado.")
        return redirect("fechamento")


def _painel(resumo, fechamento):
    if fechamento is None:
        return {
            "total": resumo.total,
            "quantidade": resumo.quantidade,
            "ticket_medio": resumo.ticket_medio,
            "canais": resumo.canais,
            "pagamentos": resumo.pagamentos,
            "mostrar_contagem": True,
        }
    return {
        "total": fechamento.total_geral,
        "quantidade": fechamento.quantidade_pedidos,
        "ticket_medio": fechamento.ticket_medio,
        "canais": (
            Grupo("ifood", "iFood", fechamento.total_ifood, 0),
            Grupo("whatsapp", "WhatsApp", fechamento.total_whatsapp, 0),
        ),
        "pagamentos": (
            Grupo("pix", "Pix", fechamento.total_pix, 0),
            Grupo("dinheiro", "Dinheiro", fechamento.total_dinheiro, 0),
            Grupo("cartao", "Cartão", fechamento.total_cartao, 0),
            Grupo("ifood_online", "Pago no iFood", fechamento.total_ifood_online, 0),
        ),
        "mostrar_contagem": False,
    }


class EstoqueView(LoginRequiredMixin, TemplateView):
    template_name = "gestao/estoque.html"

    def get_context_data(self, **kwargs):
        insumos = list(Insumo.objects.all())
        contexto = super().get_context_data(**kwargs)
        contexto["insumos"] = insumos
        contexto["alertas"] = sum(1 for insumo in insumos if insumo.abaixo_do_minimo)
        contexto["movimentos"] = MovimentacaoEstoque.objects.select_related("insumo")[:8]
        return contexto

    def post(self, request, *args, **kwargs):
        tipo = request.POST.get("tipo", "")
        try:
            insumo = Insumo.objects.get(pk=request.POST.get("insumo_id"))
            quantidade = analisar_quantidade(request.POST.get("quantidade", ""))
            registrar_movimentacao(insumo, tipo, quantidade)
        except (Insumo.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Insumo não encontrado.")
        except ErroNegocio as exc:
            messages.error(request, str(exc))
        else:
            if tipo == MovimentacaoEstoque.Tipo.ENTRADA:
                messages.success(request, "Entrada registrada.")
            else:
                messages.success(request, "Saída registrada.")
        return redirect("estoque")
