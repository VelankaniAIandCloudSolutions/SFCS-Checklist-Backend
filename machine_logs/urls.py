from django.urls import path
from . import views

urlpatterns = [
    path('create-board-log/', views.create_board_log),
    path('get-board-logs/', views.get_board_logs),
    path('get-machine-list/', views.get_machine_list),
    path('get-machine-reports-by-date-range/',
         views.get_machine_reports_by_date_range),
]
