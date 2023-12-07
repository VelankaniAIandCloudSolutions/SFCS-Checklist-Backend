from django.urls import path 
from store_checklist import views

urlpatterns= [
    path('upload-bom/', views.upload_bom),
     path('get-boms/', views.get_boms, name='get-boms'),
]

