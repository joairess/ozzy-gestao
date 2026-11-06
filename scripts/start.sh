#!/usr/bin/env bash
# Sobe o Ozzy Gestão: aplica migrações, recria a demonstração e escuta em $PORT.
# O disco do plano gratuito é efêmero, então o seed roda em todo boot.
set -o errexit

python manage.py migrate --noinput
python manage.py seed_demo

# Um único worker: o SQLite não suporta vários processos gravando ao mesmo tempo.
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 1
