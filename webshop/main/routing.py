from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/multiplayer/(?P<room_name>\w+)/$', consumers.MultiplayerConsumer.as_asgi()),
]