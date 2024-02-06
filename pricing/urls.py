from django.urls import path
from .views import *

urlpatterns = [
    path('get-project-pricing-page', get_project_pricing_page),
    path('get-product-pricing/<int:product_id>/', get_product_pricing),
    path('get-project-pricing/<int:project_id>/', get_project_pricing),
    path('refresh-product-pricing', refresh_product_pricing),
]
