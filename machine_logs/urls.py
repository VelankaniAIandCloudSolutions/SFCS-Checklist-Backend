from django.urls import path
from . import views

urlpatterns = [
    path('get-machines-logs/', views.get_machine_logs),
]
