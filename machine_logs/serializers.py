from rest_framework import serializers
from .models import Board, Panel, BoardLog
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


class BoardLogSerializer(serializers.ModelSerializer):
    machines = MachineSerializer(many=True)
    panel = PanelSerializer()
    date = serializers.DateField()
    class Meta:
        model = BoardLog
        fields = '__all__'
