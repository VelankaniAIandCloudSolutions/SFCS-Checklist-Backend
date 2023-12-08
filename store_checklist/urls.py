from django.urls import path 
from store_checklist import views

urlpatterns= [
    path('upload-bom/', views.upload_bom),
    path('scan-code/', views.scan_code),
    path('generate-new-checklist/<int:bom_id>/', views.generate_new_checklist),
    path('get-active-checklist/<int:bom_id>/', views.get_active_checklist),
]

