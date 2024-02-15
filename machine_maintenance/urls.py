from django.urls import path
# from .views import *
from . import views

urlpatterns = [
    path('get-machine-data/', views.get_machine_data),
    path('create-maintenance-plan/', views.create_maintenance_plan),
    path('get-maintenance-plan/', views.get_maintenance_plan),
    path('create-or-delete-maintenance-activity',
         views.create_or_delete_maintenance_activity),


]
