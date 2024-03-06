from django.urls import path
from .consumers import ChecklistConsumer

websocket_urlpatterns = [
    path('ws/checklist/', ChecklistConsumer.as_asgi()),
]
        