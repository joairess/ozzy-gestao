"""Configurações do Ozzy Gestão.

SQLite é o padrão local e do deploy gratuito no Render. Defina
DATABASE_URL para usar PostgreSQL. Segredos vêm do ambiente ou de um
arquivo .env local, que não é versionado.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from config.database import config_banco
from config.env import carregar_env
from config.producao import (
    CHAVE_SECRETA_DEV,
    chave_secreta,
    debug_ligado,
    montar_allowed_hosts,
    montar_origens_csrf,
)

BASE_DIR = Path(__file__).resolve().parent.parent

carregar_env(BASE_DIR / ".env")

EM_RENDER = bool(os.environ.get("RENDER"))

SECRET_KEY = chave_secreta(
    os.environ.get("DJANGO_SECRET_KEY"),
    os.environ.get("SECRET_KEY"),
)
DEBUG = debug_ligado(os.environ.get("DJANGO_DEBUG"), EM_RENDER)
ALLOWED_HOSTS = montar_allowed_hosts(
    os.environ.get("DJANGO_ALLOWED_HOSTS"),
    os.environ.get("RENDER_EXTERNAL_HOSTNAME"),
)
CSRF_TRUSTED_ORIGINS = montar_origens_csrf(
    os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS"),
    os.environ.get("RENDER_EXTERNAL_URL"),
)

if EM_RENDER and SECRET_KEY == CHAVE_SECRETA_DEV:
    raise ImproperlyConfigured(
        "Defina DJANGO_SECRET_KEY (ou SECRET_KEY) no ambiente do Render."
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "gestao",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    *(
        ["whitenoise.middleware.WhiteNoiseMiddleware"]
        if not DEBUG
        else []
    ),
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

try:
    DATABASES = {
        "default": config_banco(os.environ.get("DATABASE_URL"), BASE_DIR / "db.sqlite3")
    }
except ValueError as exc:
    raise ImproperlyConfigured(str(exc)) from exc

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "novo_pedido"
LOGOUT_REDIRECT_URL = "login"

# Cookies de sessão só trafegam em HTTPS quando o modo debug está desligado.
# No Render o TLS termina na borda; o processo recebe HTTP com este cabeçalho.
SESSION_COOKIE_HTTPONLY = True
if EM_RENDER:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
