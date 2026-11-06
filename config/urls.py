from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def saude(_request):
    return HttpResponse("ok", content_type="text/plain; charset=utf-8")


urlpatterns = [
    path("saude/", saude, name="saude"),
    path("admin/", admin.site.urls),
    path("", include("gestao.urls")),
]
