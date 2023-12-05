from django.urls import path 
from store_checklist import views

urlpatterns= [
    path('test-api/', views.test_api),
]

