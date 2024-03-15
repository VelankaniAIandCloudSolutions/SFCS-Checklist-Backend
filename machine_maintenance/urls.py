from django.urls import path
# from .views import *
from . import views

urlpatterns = [
    path('get-machine-data/', views.get_machine_data),
    path('create-maintenance-plan/', views.create_maintenance_plan),
    path('create-maintenance-plan-for-all-machines-of-a-line/',
         views.create_maintenance_plan_for_all_machines_of_a_line),
    path('get-maintenance-plan/', views.get_maintenance_plan),
    path('get-maintenance-plan-new-line-wise/',
         views.get_maintenance_plan_new_line_wise),

    path('create-maintenance-activity', views.create_maintenance_activity),
    path('create-maintenance-activity-new-for_all_machines_of_a_line',
         views.create_maintenance_activity_new_for_all_machines_of_a_line),
    path('update-or-delete-maintenance-activity/<int:maintenance_plan_id>/',
         views.update_or_delete_maintenance_activity),
    path('delete-maintenance-plan/<int:maintenance_plan_id>/',
         views.delete_maintenance_plan),
    path('create-maintenance-plan-by-clicking/',
         views.create_maintenance_plan_by_clicking),
    path('test-mail/', views.test_maintenance_alert_email),
    path('get-maintenance-plans-for-report-generation/',
         views.get_maintenance_plans_for_report_generation),
]
