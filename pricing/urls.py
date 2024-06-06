from django.urls import path
from .views import *

urlpatterns = [
    path('get-project-pricing-page', get_project_pricing_page),
    path('refresh-product-pricing', refresh_product_pricing),
    path('get-product-pricing/<int:product_id>/', get_product_pricing),
    path('get-product-pricing/<int:product_id>/', get_product_pricing),
    path('get-bom-pricing/<int:bom_id>/', get_bom_pricing),
    path('create-mfr-part-distributor-data', create_mfr_part_distributor_data)
]
