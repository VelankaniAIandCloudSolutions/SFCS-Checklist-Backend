from rest_framework import serializers
from .models import Board, Panel, MachineLog
from store_checklist.serializers import ProductSerializer
from machine_maintenance.serializers import MachineSerializer


class BoardSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = Board
        fields = '__all__'


class PanelSerializer(serializers.ModelSerializer):
    board = BoardSerializer()

    class Meta:
        model = Panel
        fields = '__all__'


class MachineLogSerializer(serializers.ModelSerializer):
    machine = MachineSerializer(many=True)
    panel = PanelSerializer()

    class Meta:
        model = MachineLog
        fields = '__all__'
