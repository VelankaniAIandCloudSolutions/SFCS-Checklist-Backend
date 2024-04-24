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
    board_serial_number = serializers.SerializerMethodField()

    def get_board_serial_number(self, obj):
        # Access the board associated with the board log and retrieve its serial_number
        return obj.panel.board.serial_number

    class Meta:
        model = BoardLog
        fields = '__all__'
        extra_fields = ['board_serial_number']
