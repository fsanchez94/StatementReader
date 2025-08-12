from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/progress/<uuid:session_id>/', consumers.ProgressConsumer.as_asgi()),
]