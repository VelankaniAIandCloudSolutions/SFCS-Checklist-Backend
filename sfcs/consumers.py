from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404

from store_checklist.models import BillOfMaterials, Checklist, ChecklistSetting
from store_checklist.serializers import ChecklistSerializer
from rest_framework import status
from rest_framework.response import Response
import json
from asgiref.sync import async_to_sync


class ChecklistConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # Add the WebSocket connection to the group
        self.group_name = 'checklist_update_group'
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

    def disconnect(self, close_code):
        # Remove the WebSocket connection from the group when disconnected
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        # You can implement any generic message handling here if needed
        pass

    def send_checklist_items(self, event):
        print('tftftft')
        # Extract checklist items from the event data
        active_checklist = event['active_checklist']
        # checklists = event['checklists']

        # Send the checklist items as JSON to the WebSocket client
        self.send(text_data=json.dumps({
            'active_checklist': active_checklist
            # 'checklists': checklist_items
        }))


class InspectionBoardConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # Add the WebSocket connection to the group
        self.group_name = 'inspection_board_create_group'
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

    def disconnect(self, close_code):
        # Remove the WebSocket connection from the group when disconnected
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        # You can implement any generic message handling here if needed
        pass

    def send_inspection_board(self, event):

        # Extract inspection board from the event data
        active_inspection_board = event['active_inspection_board']
        all_inspection_boards = event['all_inspection_boards']
 # Send the inspection board and all inspection boards as JSON to the WebSocket client
        self.send(text_data=json.dumps({
            'active_inspection_board': active_inspection_board,
            'all_inspection_boards': all_inspection_boards
        }))
