from django.urls import path 
from store_checklist import views

urlpatterns= [
    path('upload-bom/', views.upload_bom),
    path('scan-code/', views.scan_code),
    path('get-boms/', views.get_boms),
    path('get-boms/<int:bom_id>/', views.get_bom_by_id),
    path('generate-new-checklist/<int:bom_id>/', views.generate_new_checklist),
    path('get-active-checklist/<int:bom_id>/', views.get_active_checklist),
    path('check-existing-checklist/<int:bom_id>/', views.check_existing_checklist),
    path('end-checklist/<int:checklist_id>/', views.end_checklist),
    path('get-checklist-details/<int:checklist_id>/', views.get_checklist_details),
]

    