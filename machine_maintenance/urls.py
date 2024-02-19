from django.urls import path
# from .views import *
from . import views

urlpatterns = [
    path('get-machine-data/', views.get_machine_data),
    path('create-maintenance-plan/', views.create_maintenance_plan),
    path('get-maintenance-plan/', views.get_maintenance_plan),
    path('create-maintenance-activity',
         views.create_maintenance_activity),
    path('update-or-delete-maintenance-activity/<int:maintenance_plan_id>/',
         views.update_or_delete_maintenance_activity),



]
