from django.apps import AppConfig


class GestaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestao"
    verbose_name = "Ozzy Gestão"

    def ready(self):
        from django.contrib import admin

        admin.site.site_header = "Ozzy Gestão"
        admin.site.site_title = "Ozzy Gestão"
        admin.site.index_title = "Cadastros"
