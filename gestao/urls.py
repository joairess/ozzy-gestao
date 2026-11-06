from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import RedirectView

from gestao.forms import FormularioLogin
from gestao.views import EstoqueView, FechamentoView, NovoPedidoView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="novo_pedido", permanent=False), name="inicio"),
    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="gestao/login.html",
            authentication_form=FormularioLogin,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("pedidos/novo/", NovoPedidoView.as_view(), name="novo_pedido"),
    path("fechamento/", FechamentoView.as_view(), name="fechamento"),
    path("estoque/", EstoqueView.as_view(), name="estoque"),
]
