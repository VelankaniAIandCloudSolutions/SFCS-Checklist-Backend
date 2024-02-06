from rest_framework import serializers
from .models import PartPricing
from store_checklist.serializers import ProjectListSerializer,ProductSerializer

class PartPricingSerializer(serializers.ModelSerializer):
    project = ProjectListSerializer()
    product = ProductSerializer()
    class Meta:
        model = PartPricing
        fields = '__all__'

    