from django.apps import AppConfig


class BuildingsConfig(AppConfig):
    default_auto_field = "django_mongodb_backend.fields.ObjectIdAutoField"
    name = "game_building.apps.buildings"
