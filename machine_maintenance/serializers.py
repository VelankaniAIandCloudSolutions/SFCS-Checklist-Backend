from django.conf import settings
from rest_framework import serializers
from .models import *


class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = '__all__'


class MachineSerializer(serializers.ModelSerializer):
    line = LineSerializer()

    class Meta:
        model = Machine
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
    class Meta:
        model = MaintenanceActivity
        fields = '__all__'


class MaintenancePlanSerializer(serializers.ModelSerializer):
    maintenance_activities = MaintenanceActivitySerializer(
        many=True, read_only=True)

    maintenance_activity_type = MaintenanceActivityTypeSerializer(
        read_only=True)

    class Meta:
        model = MaintenancePlan
        fields = '__all__'
