from django import template

from gestao.formatacao import data_por_extenso, quantidade_br, reais

register = template.Library()

register.filter("reais", reais)
register.filter("qtd_br", quantidade_br)
register.filter("data_extenso", data_por_extenso)
