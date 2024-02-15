from django.conf import settings
from rest_framework import serializers
from .models import *
from accounts.serializers import UserAccountSerializer


class MachineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Machine
        fields = '__all__'


class LineSerializer(serializers.ModelSerializer):
    machines = MachineSerializer(many=True, read_only=True)

    class Meta:
        model = Line
        fields = '__all__'


class ModelSerializer(serializers.ModelSerializer):
    machine = MachineSerializer()  # Serialize the associated Machine object
    # Serialize the associated Line object directly from Model's machine

    class Meta:
        model = Model
        fields = '__all__'


class MaintenanceActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceActivityType
        fields = '__all__'


class MaintenanceActivitySerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    created_by = UserAccountSerializer()
    updated_by = UserAccountSerializer()

    class Meta:
        model = MaintenanceActivity
        fields = '__all__'


class MaintenancePlanSerializer(serializers.ModelSerializer):
    maintenance_activities = MaintenanceActivitySerializer(
        many=True, read_only=True)

    maintenance_activity_type = MaintenanceActivityTypeSerializer(
        read_only=True)

    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    created_by = UserAccountSerializer()
    updated_by = UserAccountSerializer()

    class Meta:
        model = MaintenancePlan
        fields = '__all__'
