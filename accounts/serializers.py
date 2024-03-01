from djoser import serializers as djoser_serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password',
                  'phone_number', 'is_superuser', 'is_staff', 'is_store_team', 'is_design_team', 'is_machine_maintenance_supervisor_team', 'is_machine_maintenance_staff_team')


class UserAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = '__all__'
