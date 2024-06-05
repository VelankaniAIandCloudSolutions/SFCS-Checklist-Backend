from rest_framework import serializers
from .models import PartPricing
from accounts.serializers import UserAccountSerializer
from store_checklist.serializers import ProjectListSerializer, ProductSerializer
from pricing.models import *


class PartPricingSerializer(serializers.ModelSerializer):
    project = ProjectListSerializer()
    product = ProductSerializer()

    class Meta:
        model = PartPricing
        fields = '__all__'


class CurrencySerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_by = UserAccountSerializer()
    created_by = UserAccountSerializer()
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = Currency
        fields = '__all__'


class PackageTypeSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_by = UserAccountSerializer()
    created_by = UserAccountSerializer()
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = PackageType
        fields = '__all__'


class ManufacturerPartDistributorDetailSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_by = UserAccountSerializer()
    created_by = UserAccountSerializer()
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = ManufacturerPartDistributorDetail
        fields = '__all__'


class DistributorPackageTypeDetailSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_by = UserAccountSerializer()
    created_by = UserAccountSerializer()
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = DistributorPackageTypeDetail
        fields = '__all__'


class ManufacturerPartPricingSerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_by = UserAccountSerializer()
    created_by = UserAccountSerializer()
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')

    class Meta:
        model = ManufacturerPartPricing
        fields = '__all__'
