from django.urls import path
from store_checklist import views

urlpatterns = [
    path('upload-bom/', views.upload_bom_task),
    path('scan-code/', views.scan_code),
    path('get-boms/', views.get_boms),
    path('get-checklist-report/', views.get_checklist_report),
    path('get-boms/<int:bom_id>/', views.get_bom_by_id),
    path('generate-new-checklist/<int:bom_id>/', views.generate_new_checklist),
    path('get-active-checklist/<int:bom_id>/', views.get_active_checklist),
    path('check-existing-checklist/<int:bom_id>/',
         views.check_existing_checklist),
    path('end-checklist/<int:checklist_id>/', views.end_checklist),
    path('get-checklist-details/<int:checklist_id>/',
         views.get_checklist_details),
    path('save-qr-code/<int:checklist_id>/', views.save_qr_code),
    path('generated-checklists/<int:bom_id>/', views.get_checklists_for_bom),
    path('get-checklist-count/', views.get_checklist_count),
    path('check-task-status/<str:task_id>/', views.check_task_status),

    path('edit-bom-line-item/<int:bom_line_item_id>/', views.edit_bom_line_item),




]
