import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "game_building.config.settings")

app = Celery("game_building.config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
