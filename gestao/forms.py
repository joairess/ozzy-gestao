"""Formulários das telas do balcão."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from gestao.models import Pedido, Produto


class FormularioLogin(AuthenticationForm):
    error_messages = {
        "invalid_login": "Usuário ou senha incorretos.",
        "inactive": "Esta conta está inativa.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Usuário"
        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "username",
                "autocapitalize": "none",
            }
        )
        self.fields["password"].label = "Senha"
        self.fields["password"].widget.attrs.update(
            {
                "class": "form-control",
                "autocomplete": "current-password",
            }
        )


def formulario_pedido(produtos: list[Produto], data=None):
    """Monta o formulário com um campo de quantidade para cada produto ativo."""
    campos = {
        "canal": forms.ChoiceField(
            label="De onde veio o pedido?",
            choices=Pedido.Canal.choices,
            widget=forms.RadioSelect,
            error_messages={"required": "Escolha de onde veio o pedido."},
        ),
        "cliente_nome": forms.CharField(
            label="Nome do cliente",
            max_length=120,
            widget=forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "maxlength": "120",
                }
            ),
            error_messages={"required": "Informe o nome do cliente."},
        ),
        "forma_pagamento": forms.ChoiceField(
            label="Como vai pagar?",
            choices=Pedido.FormaPagamento.choices,
            widget=forms.RadioSelect,
            error_messages={"required": "Escolha a forma de pagamento."},
        ),
    }
    for produto in produtos:
        campos[f"qtd_{produto.id}"] = forms.IntegerField(
            label=produto.nome,
            min_value=0,
            max_value=99,
            required=False,
            initial=0,
            widget=forms.NumberInput(
                attrs={
                    "class": "form-control campo-quantidade",
                    "inputmode": "numeric",
                    "min": "0",
                    "max": "99",
                    "data-preco": str(produto.preco),
                }
            ),
            error_messages={
                "min_value": "A quantidade não pode ser negativa.",
                "max_value": "A quantidade máxima por produto é 99.",
                "invalid": "Informe a quantidade só com números.",
            },
        )
    classe = type("FormularioPedido", (forms.Form,), campos)
    if data is None:
        return classe()
    return classe(data)
