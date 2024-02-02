from django.urls import path
from .views import *

urlpatterns = [
    path('get-product-pricing/<int:product_id>/', get_product_pricing),
]
