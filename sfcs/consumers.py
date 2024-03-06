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
        # Extract checklist items from the event data
        checklist_items = event['checklist_items']

        # Send the checklist items as JSON to the WebSocket client
        self.send(text_data=json.dumps({
            'checklist_items': checklist_items
        }))
        # text_data_json = json.loads(text_data)
        # message = text_data_json['message']
        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
        # print('called')
        # print(text_data)
        # try:
        #     data = json.loads(text_data)
        #     bom_id = data.get('bom_id')
        #     print('Received bom_id:', bom_id)
        # except json.JSONDecodeError:
        #     print('Invalid JSON data received:', text_data)
        # bom_id = text_data.get('bom_id') 
        # try:
        #     setting = ChecklistSetting.objects.first()
        #     bom = BillOfMaterials.objects.get(id=bom_id)
        #     if (setting.active_bom == bom):
        #         checklist = Checklist.objects.get(pk=setting.active_checklist.id)

        #         if (ChecklistConsumer.is_checklist_complete(checklist)):
        #             checklist.is_passed = True
        #             checklist.status = 'Completed'
        #             checklist.save()

        #         checklist_serializer = ChecklistSerializer(checklist)

        #         self.send(text_data=checklist_serializer.data)
        #     else:
        #         self.send(text_data={'error': 'No active BOM found'})

        # except ChecklistSetting.DoesNotExist:
        #     batch_quantity = text_data.get('batch_quantity') or 1
        #     setting = ChecklistSetting.objects.create(
        #         active_bom=BillOfMaterials.objects.get(id=bom_id), created_by=self.scope['user'], updated_by=self.scope['user'])
        #     setting.active_checklist = Checklist.objects.create(
        #         bom=BillOfMaterials.objects.get(id=bom_id), status='In Progress', created_by=self.scope['user'], updated_by=self.scope['user'], batch_quantity=batch_quantity)
        #     setting.save()
        #     self.send(text_data={'message': 'Active Checklist and BOM not defined but new ones set successfully'})

        # except BillOfMaterials.DoesNotExist:
        #     self.send(text_data={'error': 'BOM not found'})


