from django.urls import path
from .consumers import ChecklistConsumer, InspectionBoardConsumer


websocket_urlpatterns = [
    path('ws/checklist/', ChecklistConsumer.as_asgi()),
    path('ws/inspection-board/', InspectionBoardConsumer.as_asgi()),

]
