from django.conf import settings
from rest_framework import serializers
from .models import *
from accounts.serializers import UserAccountSerializer


class LineSerializerNew(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = '__all__'


class MachineSerializerNew(serializers.ModelSerializer):
    line = LineSerializerNew()  # Include the LineSerializer for the line field

    class Meta:
        model = Machine
        fields = '__all__'


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'


class LineSerializer(serializers.ModelSerializer):
    machines = MachineSerializer(many=True, read_only=True)

    class Meta:
        model = Line
        fields = '__all__'

    def get_machines(self, obj):
        machines = obj.machines.all()
        machine_serializer = MachineSerializer(machines, many=True)
        return machine_serializer.data


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

    maintenance_activity_type = MaintenanceActivityTypeSerializer(
        read_only=True)
    created_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    updated_at = serializers.DateTimeField(format='%d/%m/%Y %H:%M:%S')
    created_by = UserAccountSerializer()
    updated_by = UserAccountSerializer()
    maintenance_activities = serializers.SerializerMethodField()
    machine = MachineSerializerNew()

    def get_maintenance_activities(self, instance):
        activities = instance.maintenance_activities.all().order_by('-created_at')
        serializer = MaintenanceActivitySerializer(activities, many=True)
        return serializer.data

    class Meta:
        model = MaintenancePlan
        fields = '__all__'
