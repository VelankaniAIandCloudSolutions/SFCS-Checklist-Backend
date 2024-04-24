from django.urls import path
from . import views

urlpatterns = [
    path('create-board-log/', views.create_board_log),
    path('get-machines-logs/', views.get_machine_logs),
]
