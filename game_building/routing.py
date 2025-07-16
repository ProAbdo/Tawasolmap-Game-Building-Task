# your_app/routing.py
from django.urls import path
from game_building.consumers import GameConsumer

websocket_urlpatterns = [
    path("ws/game/", GameConsumer.as_asgi()),
]
