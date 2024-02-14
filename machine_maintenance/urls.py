from django.urls import path
# from .views import *
from . import views

urlpatterns = [
    path('get-machine-data/', views.get_machine_data),
    path('create-maintenance-activity/', views.create_maintenance_activity),
    path('get-maintenance-plan/', views.get_maintenance_plan),

]
