
from io import BytesIO
from .models import Checklist, ChecklistSetting
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import BillOfMaterialsLineItemSerializer, ManufacturerPartSerializer, BillOfMaterialsLineItemReferenceSerializer, BillOfMaterialsLineItemTypeSerializer, ChecklistWithoutItemsSerializer
from .models import BillOfMaterialsLineItem, ManufacturerPart, BillOfMaterialsLineItemReference, BillOfMaterialsLineItemType
from django.db import transaction
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import *
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .serializers import *
import pandas as pd
import json
from django.db.models import Q
import re
from .tasks import process_bom_file, process_bom_file_new,  test_func, process_bom_file_and_create_order, process_bom_file_and_create_order_new
import os
from django.conf import settings
from celery.result import AsyncResult
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from accounts.models import *
from .tasks import *


@api_view(['POST'])
def handle_bom_cases(request):
    print('this is request.data', request.data)
    try:
        # Check if the BOM already exists
        print(request.data)
        product_id = request.data.get('product_id')
        bom_rev_number = request.data.get('bom_rev_no')
        print('this is product id=', product_id)
        print('this is bom_rev_number id=', bom_rev_number)

        existing_bom = BillOfMaterials.objects.get(
            product_id=product_id, bom_rev_number=bom_rev_number)

        # Case 1: BOM already exists
        return Response({'message': f'BOM already exists with REV No: {existing_bom.bom_rev_number}', 'bom_rev_number': existing_bom.bom_rev_number
                         }, status=200)
    except ObjectDoesNotExist:
        # Check if it's a new BOM revision number
        if BillOfMaterials.objects.filter(product_id=product_id).exists():
            # Case 2: New BOM revision number, return JSON response
            return Response({'message': 'New BOM revision number for an existing product.'}, status=201)
        else:
            # Case 3: New BOM revision number, no BOM uploaded yet, return JSON response
            return Response({'message': 'New BOM revision number, no BOM uploaded yet.'}, status=204)
# @api_view(['POST'])
# def handle_bom_cases(request):
#     print(request.data)

#     # Check if the BOM already exists
#     print(request.data)
#     product_id = request.data.get('product_id')
#     bom_rev_number = request.data.get('bom_rev_number')
#     print(product_id)

#     if BillOfMaterials.objects.filter(product_id=product_id, bom_rev_number=bom_rev_number).exists():
#         # Case 1: BOM already exists
#         return Response({'message': f'BOM already exists with REV No: {bom_rev_number}'}, status=200)

#     # Check if it's a new BOM revision number for an existing product
#     elif BillOfMaterials.objects.filter(product_id=product_id).exists():
#         # Case 2: New BOM revision number, return JSON response
#         return Response({'message': 'New BOM revision number for an existing product.'}, status=201)

#     # Case 3: New BOM revision number, no BOM uploaded yet, return JSON response
#     else:
#         return Response({'message': 'New BOM revision number, no BOM uploaded yet.'}, status=404)


@api_view(['POST'])
def upload_bom_task(request):
    # try:
    test_func.delay(5,6)
    bom_file = request.FILES.get('bom_file')
    print('this is bom file', bom_file)

    pcb_file = request.FILES.get('pcb_file')
    print('this is pcb file', pcb_file)

    bom_file_name = str(request.FILES['bom_file'].name)
    if bom_file is None:
        return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

    media_directory = os.path.join('bom_files', bom_file_name)

    bom_file_path = os.path.join(settings.MEDIA_ROOT, media_directory)

    os.makedirs(os.path.dirname(bom_file_path), exist_ok=True)

    with open(bom_file_path, 'wb') as destination:
        for chunk in bom_file.chunks():
            destination.write(chunk)

    bom_path = str(bom_file_path)

    pcb_file_name = None
    pcb_path = None
    if pcb_file:
        pcb_file_name = str(request.FILES['pcb_file'].name)
        pcb_media_directory = os.path.join(
            'pcb_bbt_test_report_files', pcb_file_name)
        pcb_file_path = os.path.join(settings.MEDIA_ROOT, pcb_media_directory)
        os.makedirs(os.path.dirname(pcb_file_path), exist_ok=True)
        with open(pcb_file_path, 'wb') as destination:
            for chunk in pcb_file.chunks():
                destination.write(chunk)
        pcb_path = str(pcb_file_path)

    bom_data = {
        'project_id': request.data.get('project_id'),
        'product_id': request.data.get('product_id'),
        'product_rev_no': request.data.get('product_rev_no'),
        'bom_type': request.data.get('bom_type'),
        'bom_rev_no': request.data.get('bom_rev_no'),
        'issue_date': request.data.get('issue_date'),
        'bom_rev_change_note': request.data.get('bom_rev_change_note'),
        'bom_format_id': request.data.get('bom_format_id'),
        'pcb_file_name': pcb_file_name,
        'pcb_file_path': pcb_path,



        # 'batch_quantity': request.data.get('batch_quantity'),
    }
    print('inside upload bom task api')
    print('project_id=', bom_data.get('project_id'))
    # print('batch quantity=', bom_data.get('batch_quantity'))

    res = process_bom_file_new.delay(
        bom_path, bom_file_name, bom_data, request.user.id)
    task_result = AsyncResult(res.id)
    task_status = task_result.status
    print(task_status)
    print(task_result)
    return Response({'message': 'BOM upload task is queued for processing', 'task_id': res.id, 'task_status': str(task_status)}, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
def check_task_status(request, task_id):
    try:

        task = AsyncResult(task_id)
        if task.state == 'PENDING':
            data = {'task_id': task_id, 'task_status': 'PENDING'}
        elif task.state == 'SUCCESS':
            data = {'task_id': task_id, 'task_status': 'SUCCESS'}
        elif task.state == 'FAILURE':
            data = {'task_id': task_id, 'task_status': 'FAILURE'}
        else:
            data = {'task_id': task_id, 'task_status': 'IN PROGRESS'}
        print(data)
        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def scan_code(request):

    print(request.data)
    # input_string = "u1UUID000128808-VEPL145154751D<Facts>Q500"
    text = request.data.get('value')
    vepl_pattern = r'(VEPL.*?)(?=1D<)'
    quantity_pattern = r'Q(\d+)'
    vepl_match = re.search(vepl_pattern, text)
    quantity_match = re.search(quantity_pattern, text)
    uid_pattern = r'UUID\d+'

    matches = re.findall(uid_pattern, text)
    if matches:
        uuid = matches[0]
        print(uuid)
    else:
        print("UUID not found in the input string.")

    if quantity_match:
        quantity = int(quantity_match.group(1))
    else:
        quantity = 0

    if vepl_match:
        part_number = vepl_match.group(1)

        print("UUID:", uuid)
        print("Part Number:", part_number)

        active_bom = ChecklistSetting.objects.first().active_bom
        active_checklist = ChecklistSetting.objects.first().active_checklist

        print("Active BOM:", active_bom)
        print("Active Checklist:", active_checklist)

        is_present = False
        is_quantity_sufficient = False

        if active_bom and active_checklist:

            if ChecklistItemUID.objects.filter(uid=uuid, checklist_item__checklist=active_checklist).exists():
                return JsonResponse({'message': f'UUID {uuid} already exists in ChecklistItemUID table'}, status=405)
            else:
                for bom_line_item in active_bom.bom_line_items.all():
                    if bom_line_item.part_number.strip() == part_number.strip():
                        is_present = True
                        if bom_line_item.line_item_type:

                            if bom_line_item.line_item_type.name.strip().upper() == 'PCB':
                                checklist_item_type_value = 'PCB'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'PCB SERIAL NUMBER LABEL':
                                checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER PASTE':
                                checklist_item_type_value = 'SOLDER PASTE'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER BAR':
                                checklist_item_type_value = 'SOLDER BAR'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'IPA':
                                checklist_item_type_value = 'IPA'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER FLUX':
                                checklist_item_type_value = 'SOLDER FLUX'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER WIRE':
                                checklist_item_type_value = 'SOLDER WIRE'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'SMT PALLET':
                                checklist_item_type_value = 'SMT PALLET'
                            elif bom_line_item.line_item_type.name.strip().upper() == 'WAVE PALLET':
                                checklist_item_type_value = 'WAVE PALLET'
                            else:
                                checklist_item_type_value = 'RAW MATERIAL'

                        checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value,
                                                                                         defaults={
                                                                                             'updated_by': request.user,
                                                                                             'created_by': request.user,
                                                                                         })

                        checklist_item, checklist_item_created = ChecklistItem.objects.get_or_create(
                            checklist=active_checklist,
                            bom_line_item=bom_line_item,
                            defaults={
                                # 'updated_by': request.user,
                                # 'created_by': request.user,
                                'checklist_item_type': checklist_item_type
                            }
                        )

                        checklist_item_uid, checklist_item_uid_created = ChecklistItemUID.objects.get_or_create(
                            checklist_item=checklist_item,
                            uid=uuid,
                        )
                        print(
                            f'ChecklistItem created: {checklist_item_created }')
                        print(
                            f'ChecklistItemUID created: {checklist_item_uid_created}')

                        if checklist_item_created:
                            checklist_item.present_quantity = quantity

                        if checklist_item_uid_created:
                            checklist_item.present_quantity += quantity

                        if checklist_item.present_quantity >= checklist_item.required_quantity:
                            is_quantity_sufficient = True

                        checklist_item.is_present = is_present
                        checklist_item.is_quantity_sufficient = is_quantity_sufficient

                        checklist_item.save()

        else:
            return Response({'error': 'No active BOM'}, status=status.HTTP_400_BAD_REQUEST)

        # latest_checklist_items = ChecklistItem.objects.filter(checklist__bom = active_bom)

        # latest_checklists = Checklist.objects.filter(bom=active_bom)
        # latest_checklists = ['1', '2']
        # latest_checklists_serialized = ChecklistSerializer( latest_checklists, many=True)
        try:
            active_checklist_serialized = ChecklistSerializer(active_checklist)

            # Send the latest checklist items via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'checklist_update_group',  # Group name defined in your WebSocket consumer
                {
                    'type': 'send_checklist_items',  # Method name defined in your WebSocket consumer
                    'active_checklist': active_checklist_serialized.data,
                }
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_409_BAD_REQUEST)
    # return Response({'message': 'Checklist item added successfully'})
        return Response({
            'uuid': uuid,
            'part_number': part_number,
            'is_present': is_present,
            'is_quantity_sufficient': is_quantity_sufficient,

        })

    else:
        print("Pattern not found in the input string.")
        return Response({'error': 'Invalid input string'}, status=401)


@api_view(['POST'])
def generate_new_checklist(request, order_id):
    try:

        order = Order.objects.get(id=order_id)
        active_bom = order.bom
        batch_quantity = order.batch_quantity
        # active_bom = BillOfMaterials.objects.get(id=bom_id)
        # batch_quantity = request.data.get('batch_quantity') or 1
        if ChecklistSetting.objects.exists():
            setting = ChecklistSetting.objects.first()
            print('exists')
        else:
            setting = ChecklistSetting.objects.create(
                active_bom=active_bom, created_by=request.user, updated_by=request.user)
            print("doesn't exist")

        if setting.active_checklist:
            return Response({'error': 'Active checklist already exists, please end that checklist to start a new one'}, status=status.HTTP_400_BAD_REQUEST)
        setting.active_bom = active_bom
        setting.active_checklist = Checklist.objects.create(
            bom=active_bom, status='In Progress', created_by=request.user, updated_by=request.user, batch_quantity=batch_quantity)
        setting.save()

        for bom_line_item in active_bom.bom_line_items.all():
            if bom_line_item.line_item_type:

                if bom_line_item.line_item_type.name.strip().upper() == 'PCB':
                    checklist_item_type_value = 'PCB'
                elif bom_line_item.line_item_type.name.strip().upper() == 'PCB SERIAL NUMBER LABEL':
                    checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
                elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER PASTE':
                    checklist_item_type_value = 'SOLDER PASTE'
                elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER BAR':
                    checklist_item_type_value = 'SOLDER BAR'
                elif bom_line_item.line_item_type.name.strip().upper() == 'IPA':
                    checklist_item_type_value = 'IPA'
                elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER FLUX':
                    checklist_item_type_value = 'SOLDER FLUX'
                elif bom_line_item.line_item_type.name.strip().upper() == 'SOLDER WIRE':
                    checklist_item_type_value = 'SOLDER WIRE'
                elif bom_line_item.line_item_type.name.strip().upper() == 'SMT PALLET':
                    checklist_item_type_value = 'SMT PALLET'
                elif bom_line_item.line_item_type.name.strip().upper() == 'WAVE PALLET':
                    checklist_item_type_value = 'WAVE PALLET'
                else:
                    checklist_item_type_value = 'RAW MATERIAL'

            checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value,
                                                                             defaults={
                                                                                 'updated_by': request.user,
                                                                                 'created_by': request.user,
                                                                             })
            checklist_item, created = ChecklistItem.objects.get_or_create(
                checklist=setting.active_checklist,
                bom_line_item=bom_line_item,
                required_quantity=bom_line_item.quantity*batch_quantity,
                defaults={
                    'updated_by': request.user,
                    'created_by': request.user,
                    'checklist_item_type': checklist_item_type
                }
            )

        return Response({'message': 'Active BOM set successfully'}, status=status.HTTP_200_OK)

    except BillOfMaterials.DoesNotExist:
        return Response({'error': 'BOM not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def check_existing_checklist(request, bom_id):
    try:

        active_bom = BillOfMaterials.objects.get(id=bom_id)
        is_existing = False
        is_active = False
        if ChecklistSetting.objects.exists():
            setting = ChecklistSetting.objects.first()
            if (Checklist.objects.filter(bom=active_bom, status='In Progress').exists()):
                is_existing = True
                for checklist in Checklist.objects.filter(bom=active_bom, status='In Progress'):
                    if setting.active_checklist == checklist:
                        is_active = True
                        break
        else:
            setting = ChecklistSetting.objects.create(
                active_bom=BillOfMaterials.objects.get(id=bom_id),
                created_by=request.user,
                updated_by=request.user)

        return Response({
            'is_existing': is_existing,
            'is_active': is_active
        }, status=status.HTTP_200_OK)

    except BillOfMaterials.DoesNotExist:
        return Response({'error': 'BOM not found'}, status=status.HTTP_404_NOT_FOUND)


def is_checklist_complete(checklist):
    # Check if all checklist items are complete
    for item in checklist.checklist_items.all():
        if not (item.is_present and item.is_quantity_sufficient):
            return False
    return True


@api_view(['GET'])
def get_active_checklist(request, bom_id):
    try:
        setting = ChecklistSetting.objects.first()
        bom = BillOfMaterials.objects.get(id=bom_id)
        if (setting.active_bom == bom):
            checklist = Checklist.objects.get(pk=setting.active_checklist.id)

            if (is_checklist_complete(checklist)):
                checklist.is_passed = True
                checklist.status = 'Completed'
                checklist.save()
                # setting = ChecklistSetting.objects.first()
                # setting.active_checklist = None
                # setting.active_bom = None
                # setting.save()
            checklist_serializer = ChecklistSerializer(checklist)

            return Response(
                {
                    'checklist': checklist_serializer.data,
                }, status=status.HTTP_200_OK
            )
        else:
            return Response({
                'error': 'No active BOM found',
            }, status=status.HTTP_400_BAD_REQUEST)

    except ChecklistSetting.DoesNotExist:
        batch_quantity = request.data.get('batch_quantity') or 1
        setting = ChecklistSetting.objects.create(
            active_bom=BillOfMaterials.objects.get(id=bom_id), created_by=request.user, updated_by=request.user)
        setting.active_checklist = Checklist.objects.create(
            bom=BillOfMaterials.objects.get(id=bom_id), status='In Progress', created_by=request.user, updated_by=request.user, batch_quantity=batch_quantity)
        setting.save()
        return Response({'message': 'Active Checklist and BOM not defined but new ones set successfully'}, status=status.HTTP_200_OK)

    except BillOfMaterials.DoesNotExist:
        return Response({'error': 'BOM not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_passed_checklists(request):
    try:
        # Retrieve all checklists where is_passed is True
        passed_checklists = Checklist.objects.filter(is_passed=True)

        # Serialize the passed checklists using the ChecklistSerializer
        serializer = ChecklistWithoutItemsSerializer(
            passed_checklists, many=True)

        # Return the serialized data as JSON
        return Response({'passed_checklists': serializer.data}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_checklist_details(request, checklist_id):
    try:
        checklist = Checklist.objects.get(pk=checklist_id)
        checklist_serializer = ChecklistSerializer(checklist)
        return Response(
            {
                'checklist': checklist_serializer.data,
            }, status=status.HTTP_200_OK
        )
    except Checklist.DoesNotExist:
        return Response({'error': 'Checklist not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_iqc_data(request, checklist_id):
    try:

        checklist = get_object_or_404(Checklist, id=checklist_id)

        # Serialize the Checklist object
        checklist_serializer = ChecklistWithoutItemsSerializer(checklist)

        checklist_uids = ChecklistItemUID.objects.filter(
            checklist_item__checklist_id=checklist_id)
        # Serialize the ChecklistItemUID objects
        checklist_uids_serializer = ChecklistItemUIDDetailedSerializer(
            checklist_uids, many=True)

        return Response({
            "checklist": checklist_serializer.data,
            "checklist_uids": checklist_uids_serializer.data
        })

    except Checklist.DoesNotExist:
        return Response({"error": "Checklist not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# @api_view(['GET'])
# def get_old_checklists(request,bom_id):

# @api_view(['POST'])
# def show_in_progress_checklist(request,bom_id):
# dont create the checklist just see if any in progress for that bom if not send response that no ongong is presnt


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_boms(request):
    try:
        # boms = BillOfMaterials.objects.all()
        # serializer = BillOfMaterialsSerializer(boms, many=True)

        boms_without_line_items = BillOfMaterials.objects.all().order_by('-created_at')
        bom_serializer = BillOfMaterialsListSerializer(
            boms_without_line_items, many=True)

        return Response({'boms': bom_serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        # Handle exceptions
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_bom_by_id(request, bom_id):
    try:
        bom = BillOfMaterials.objects.get(id=bom_id)
        serializer = BillOfMaterialsDetailedSerializer(bom)
        return Response({'bom': serializer.data}, status=status.HTTP_200_OK)

    except BillOfMaterials.DoesNotExist:
        # Handle the case where the BOM with the given ID does not exist
        return Response({'error': 'BOM not found'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # Handle other exceptions
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def end_checklist(request, checklist_id):
    try:
        checklist = Checklist.objects.get(id=checklist_id)
        if is_checklist_complete(checklist):
            checklist.is_passed = True
            checklist.status = 'Completed'
            checklist.save()
        else:
            checklist.status = 'Failed'
            checklist.save()

        if ChecklistSetting.objects.exists():
            setting = ChecklistSetting.objects.first()
        else:
            setting = ChecklistSetting.objects.create(
                active_bom=BillOfMaterials.objects.get(id=checklist.bom.id), created_by=request.user, updated_by=request.user)

        setting.active_bom = None
        setting.active_checklist = None
        setting.save()

        checklist_serializer = ChecklistWithoutItemsSerializer(checklist)
        return Response({'checklist': checklist_serializer.data}, status=status.HTTP_200_OK)

    except Checklist.DoesNotExist:
        return Response({'error': 'Checklist not found'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_checklists_for_bom(request, bom_id):
    try:
        # Get the BillOfMaterials object or return a 404 response if not found
        bom = get_object_or_404(BillOfMaterials, id=bom_id)

        # Retrieve all checklists associated with the specified BOM
        checklists = Checklist.objects.filter(bom=bom).order_by('-updated_at')

        # Serialize the checklists using ChecklistSerializer
        serializer = ChecklistWithoutItemsSerializer(checklists, many=True)

        # Return the serialized data as JSON response
        return Response(serializer.data)

    except Checklist.DoesNotExist:
        return Response({"error": f"Checklists for BOM with ID {bom_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    except BillOfMaterials.DoesNotExist:
        return Response({"error": f"BOM with ID {bom_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        # Handle other exceptions
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_checklist_report(request):
    try:
        checklists = Checklist.objects.all().order_by('-created_at')
        checklist_serializer = ChecklistSerializer(checklists, many=True)
        return Response({
            'checklists': checklist_serializer.data,
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def save_qr_code(request, checklist_id):
    try:
        print(request.data)
        checklist = Checklist.objects.get(pk=checklist_id)
        checklist.qr_code_link = request.data.get('qrCodeDataURL', None)
        checklist.unique_code = request.data.get('uniqueCode', None)
        checklist.save()
        checklist_serializer = ChecklistSerializer(checklist)
        return Response({'checklist': checklist_serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def get_checklist_count(request):
    selected_option = request.data.get('selected_option')

    def get_checklists_for_status(status, start_date, end_date):
        checklists = Checklist.objects.filter(
            status=status,
            updated_at__range=[start_date, end_date]
        )
        return checklists

    if selected_option == 'Today':
        today = timezone.now().date()
        in_progress_checklists = get_checklists_for_status(
            'In Progress', today, today)
        completed_checklists = get_checklists_for_status(
            'Completed', today, today)
        failed_checklists = get_checklists_for_status('Failed', today, today)
        response_data = {
            'in_progress': ChecklistWithoutItemsSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistWithoutItemsSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistWithoutItemsSerializer(failed_checklists, many=True).data,
        }

    elif selected_option == 'Previous_Week':
        today = timezone.now().date()
        last_week_start = today - timezone.timedelta(days=today.weekday() + 6)
        in_progress_checklists = get_checklists_for_status(
            'In Progress', last_week_start, today)
        completed_checklists = get_checklists_for_status(
            'Completed', last_week_start, today)
        failed_checklists = get_checklists_for_status(
            'Failed', last_week_start, today)
        response_data = {
            'in_progress': ChecklistWithoutItemsSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistWithoutItemsSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistWithoutItemsSerializer(failed_checklists, many=True).data,
        }
    elif selected_option == 'Previous_Month':
        today = timezone.now().date()
        previous_month_start = today - timezone.timedelta(days=30)
        previous_month_end = today
        in_progress_checklists = get_checklists_for_status(
            'In Progress', previous_month_start, previous_month_end)
        completed_checklists = get_checklists_for_status(
            'Completed', previous_month_start, previous_month_end)
        failed_checklists = get_checklists_for_status(
            'Failed', previous_month_start, previous_month_end)

        response_data = {
            'in_progress': ChecklistWithoutItemsSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistWithoutItemsSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistWithoutItemsSerializer(failed_checklists, many=True).data,
        }
    elif selected_option == 'Custom':
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)

        in_progress_checklists = get_checklists_for_status(
            'In Progress', start_date, end_date)
        completed_checklists = get_checklists_for_status(
            'Completed', start_date, end_date)
        failed_checklists = get_checklists_for_status(
            'Failed', start_date, end_date)

        response_data = {
            'in_progress': ChecklistWithoutItemsSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistWithoutItemsSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistWithoutItemsSerializer(failed_checklists, many=True).data,
        }

    else:
        return JsonResponse({'error': 'Invalid option'}, status=400)

    return JsonResponse(response_data)

# crud for bom_line_items:


# @api_view(['GET', 'PUT', 'DELETE'])
# @authentication_classes([])
# @permission_classes([])
# def bill_of_materials_line_item_detail(request, pk):
#     try:
#         line_item = BillOfMaterialsLineItem.objects.get(pk=pk)
#     except BillOfMaterialsLineItem.DoesNotExist:
#         return Response(status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'GET':
#         serializer = BillOfMaterialsLineItemSerializer(line_item)
#         return Response(serializer.data)

#     elif request.method == 'PUT':
#         serializer = BillOfMaterialsLineItemSerializer(
#             line_item, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     elif request.method == 'DELETE':
#         line_item.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(['GET'])
# @authentication_classes([])
# @permission_classes([])
# def get_line_item_data(request):
#     if request.method == 'GET':
#         # Fetch line item types
#         line_item_types = BillOfMaterialsLineItemType.objects.all()
#         types_serializer = BillOfMaterialsLineItemTypeSerializer(
#             line_item_types, many=True)

#         # Fetch references
#         references = BillOfMaterialsLineItemReference.objects.all()
#         references_serializer = BillOfMaterialsLineItemReferenceSerializer(
#             references, many=True)

#         return Response({
#             'line_item_types': types_serializer.data,
#             'references': references_serializer.data
#         }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@authentication_classes([])
@permission_classes([])
def edit_bom_line_item(request, bom_line_item_id):
    bom_line_item = BillOfMaterialsLineItem.objects.get(pk=bom_line_item_id)
    bom_line_item_serializer = BillOfMaterialsLineItemSerializer(bom_line_item)

    if request.method == 'GET':
        manufacturer_parts = ManufacturerPart.objects.all()
        manufacturer_part_serializer = ManufacturerPartSerializer(
            manufacturer_parts, many=True)

        line_item_types = BillOfMaterialsLineItemType.objects.all()
        types_serializer = BillOfMaterialsLineItemTypeSerializer(
            line_item_types, many=True)

        assembly_stages = AssemblyStage.objects.all()
        assembly_stages_serializer = AssemblyStageSerializer(
            assembly_stages, many=True)

        return Response({
            'bom_line_item': bom_line_item_serializer.data,
            'line_item_types': types_serializer.data,
            'manufacturers_parts': manufacturer_part_serializer.data,
            'assembly_stages': assembly_stages_serializer.data

        }, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Update the line item object with the form data from the request.data dictionary.
        # Note that the form data is a JSON object, so we need to access the fields using the keys.
        # For example, to access the part_number field, we would use request.data['part_number'].
        # Similarly, to access the level field, we would use request.data['level'].
        # And so on.
        # You can access all the fields of the form data using the keys of the JSON object.
        # For example, to access the part_number field, we would use request.data['part_number'].
        # Similarly, to access the level field, we would use request.data['level'].
        # And so on.
        # You can access all the fields of the form data using the keys of the JSON object.
        # For example, to access the part_number field, we would use request.data['part_number'].
        # Similarly, to access the level field, we would use request.data['level'].
        # And so on.
        form_data = request.data
        print('hiiiiii', form_data)
        bom_line_item.part_number = form_data['part_number']
        bom_line_item.level = form_data['level']
        bom_line_item.priority_level = form_data['priority_level']
        bom_line_item.value = form_data['value']
        bom_line_item.pcb_footprint = form_data['pcb_footprint']
        bom_line_item.description = form_data['description']
        bom_line_item.customer_part_number = form_data['customer_part_number']
        bom_line_item.quantity = form_data['quantity']
        bom_line_item.uom = form_data['uom']
        bom_line_item.ecn = form_data['ecn']
        bom_line_item.msl = form_data['msl']
        bom_line_item.remarks = form_data['remarks']
        bom_line_item.line_item_type = BillOfMaterialsLineItemType.objects.get(
            pk=form_data['line_item_type']
        )
        bom_line_item.assembly_stage = AssemblyStage.objects.get(
            pk=form_data['assembly_stage'])

        # Update many-to-many relationship (manufacturer_parts)
        manufacturer_parts_data = form_data.get('manufacturer_parts', [])
        bom_line_item.manufacturer_parts.clear()  # Clear existing relationships

        for part_data in manufacturer_parts_data:
            part_id = part_data.get('id')
            if part_id:
                manufacturer_part = ManufacturerPart.objects.get(pk=part_id)
            else:
                part_number = part_data.get('part_number')
                manufacturer = part_data.get('manufacturer')

                manufacturer_part = ManufacturerPart.objects.create(
                    part_number=part_number,
                    manufacturer=manufacturer,
                    created_by=request.user,
                    updated_by=request.user,
                    # bom_line_item=bom_line_item
                )

            bom_line_item.manufacturer_parts.add(manufacturer_part)

        # Update references from the updated data

        references_data = form_data['references']
        for reference_data in references_data:
            reference_id = reference_data.get('id')
            if reference_id:
                reference = BillOfMaterialsLineItemReference.objects.get(
                    pk=reference_id)
            else:
                reference_name = reference_data['name']
                reference = BillOfMaterialsLineItemReference.objects.create(
                    name=reference_name, bom_line_item=bom_line_item, created_by=request.user, updated_by=request.user,
                )

        bom_line_item.save()

        return Response({'message': 'BOM line item updated successfully'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@authentication_classes([])
@permission_classes([])
def delete_bom_line_item(request, bom_line_item_id):
    try:
        bom_line_item = BillOfMaterialsLineItem.objects.get(
            pk=bom_line_item_id)
    except BillOfMaterialsLineItem.DoesNotExist:
        return Response({'message': 'BOM Line Item not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        bom_line_item.delete()
        return Response({'message': 'BOM Line Item deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT'])
def update_checklist_item(request, checklist_item_id):
    try:
        checklist_item = ChecklistItem.objects.get(id=checklist_item_id)
        present_quantity = int(request.data.get('present_quantity', 0))
        change_note = request.data.get('reason_for_change')
        is_issued_to_production = request.data.get('is_issued_to_production')
        print('this is is_issued to producrtion coming from frontend',
              is_issued_to_production)

        # Ensure change note is not empty
        if not change_note and not is_issued_to_production:
            return Response({'message': 'Error: Please provide the change note, as it cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        checklist_item.present_quantity = present_quantity
        checklist_item.present_quantity_change_note = change_note

        checklist_item.is_present = checklist_item.present_quantity > 0
        checklist_item.is_quantity_sufficient = checklist_item.present_quantity >= checklist_item.required_quantity
        checklist_item.is_issued_to_production = is_issued_to_production

        checklist_item.save()

        print('value after saving', checklist_item.is_issued_to_production)
        updated_items = ChecklistItem.objects.filter(
            checklist=checklist_item.checklist)
        # Serialize the updated checklist item
        serializer = ChecklistItemSerializer(updated_items, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except ChecklistItem.DoesNotExist:
        return Response({'message': 'Checklist item not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({'message': 'Invalid present quantity'}, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['PUT'])
# def update_checklist_item(request, checklist_item_id):
#     try:
#         checklist_item = ChecklistItem.objects.get(id=checklist_item_id)
#         present_quantity = int(request.data.get('present_quantity', 0))
#         change_note = request.data.get('reason_for_change')
#         is_issued_to_production = request.data.get('is_issued_to_production')

#         if is_issued_to_production == 'true':
#             is_issued_to_production = True
#             change_note = ""  # Empty change note if issued to production

#             # Set present quantity to required quantity if issued to production
#             checklist_item.present_quantity = checklist_item.required_quantity
#         else:
#             is_issued_to_production = False
#             checklist_item.present_quantity = present_quantity

#         # Update other fields
#         checklist_item.present_quantity_change_note = change_note
#         checklist_item.is_issued_to_production = is_issued_to_production
#         checklist_item.is_present = checklist_item.present_quantity > 0
#         checklist_item.is_quantity_sufficient = checklist_item.present_quantity >= checklist_item.required_quantity

#         checklist_item.save()

#         updated_items = ChecklistItem.objects.filter(
#             checklist=checklist_item.checklist)
#         serializer = ChecklistItemSerializer(updated_items, many=True)

#         return Response(serializer.data, status=status.HTTP_200_OK)
#     except ChecklistItem.DoesNotExist:
#         return Response({'message': 'Checklist item not found'}, status=status.HTTP_404_NOT_FOUND)
#     except ValueError:
#         return Response({'message': 'Invalid present quantity'}, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['GET'])
# def get_projects(request):
#     try:
#         if request.method == 'GET':
#             projects = Project.objects.all()
#             project_serializer = ProjectSerializer(projects, many=True)
#             return Response({'projects': project_serializer.data}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# def get_products_by_project(request, project_id):
#     try:
#         if request.method == 'GET':
#             products = Product.objects.filter(project_id=project_id)
#             serialized_products = ProductSerializer(products, many=True).data
#             return Response({'products': serialized_products}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# @authentication_classes([])
# @permission_classes([])
# def get_orders(request):
#     try:
#         orders = Order.objects.all()
#         serializer = OrderSerializer(orders, many=True)
#         return JsonResponse({'orders': serializer.data}, status=200)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


# @api_view(['GET'])
# @authentication_classes([])
# @permission_classes([])
# def get_boms_without_line_items(request):
#     try:
#         # Fetch Bill of Materials without line items
#         boms_without_line_items = BillOfMaterials.objects.all()
#         serializer = BillOfMaterialsListSerializer(
#             boms_without_line_items, many=True)

#         # Return JSON with key "boms"
#         return Response({"boms": serializer.data}, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['GET'])
# def get_products(request):
#     try:
#         if request.method == 'GET':
#             products = Product.objects.all()
#             serializer = ProductSerializer(products, many=True)
#             return Response({'products': serializer.data}, status=status.HTTP_200_OK)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['GET'])
# def project_list_with_products(request):
#     projects = Project.objects.all()
#     project_data = []

#     for project in projects:
#         project_serializer = ProjectSerializer(project).data
#         products_serializer = ProductSerializer(
#             project.products.all(), many=True).data
#         project_data.append({
#             'project': project_serializer,
#             'products': products_serializer,
#         })

#     return Response(project_data, status=status.HTTP_200_OK)
@api_view(['POST'])
def create_project(request):
    try:
        # Extract data from the request data
        project_data = {
            'name': request.data.get('name', ''),
            'project_code': request.data.get('project_code', ''),
            # 'project_rev_number': request.data.get('project_rev_number', ''),
            # Add more fields as needed
        }

        # Create a new Project instance
        project = Project.objects.create(
            **project_data, created_by=request.user, updated_by=request.user)

        # Serialize the project data
        project_serializer = ProjectSerializer(project)

        # Return a success message with the created project data
        return Response({'project': project_serializer.data}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def edit_project(request, project_id=None):
    try:
        if request.method == 'GET':
            if project_id:
                # Handle GET request to retrieve a specific project by ID
                project = Project.objects.get(id=project_id)
                project_serializer = ProjectSerializer(project)
                return Response({'project': project_serializer.data}, status=status.HTTP_200_OK)
            else:
                # Handle GET request without an ID to retrieve a list of all projects
                projects = Project.objects.all()
                project_serializer = ProjectSerializer(projects, many=True)
                return Response({'projects': project_serializer.data}, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            # Handle PUT request to update an existing project
            # Extract and update the project data from request.data
            # Example: project.name = request.data.get('name', project.name)
            # ...
            # Save the updated
            project = Project.objects.get(id=project_id)

            # Update project fields based on request data
            project.name = request.data.get('name', project.name)
            project.project_code = request.data.get(
                'project_code', project.project_code)
            project.project_rev_number = request.data.get(
                'project_rev_number', project.project_rev_number)
            project.updated_by = request.user

            project.save()

            project_serializer = ProjectSerializer(project)
            return Response({'project': project_serializer.data}, status=status.HTTP_200_OK)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def edit_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        product_serializer = ProductSerializer(product)
        return Response({'product': product_serializer.data}, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Handle updating the product
        updated_product_data = {
            'name': request.data.get('name', product.name),
            'product_code': request.data.get('product_code', product.product_code),
            'product_rev_number': request.data.get('product_rev_number', product.product_rev_number),
            'project': product.project,
        }

        try:
            product.name = updated_product_data['name']
            product.product_code = updated_product_data['product_code']
            product.product_rev_number = updated_product_data['product_rev_number']
            product.updated_by = request.user
            product.save()
            product_serializer = ProductSerializer(product)
            return Response({'product': product_serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_project(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        project.delete()
        return Response({'message': 'Project deleted successfully'}, status=status.HTTP_200_OK)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['GET', 'POST'])
# def create_product(request, project_id=None):
#     try:
#         if request.method == 'GET':
#             # Handle GET request to retrieve all products or a specific product by ID
#             if project_id:
#                 product = Product.objects.get(id=project_id)
#                 product_serializer = ProductSerializer(product)

#                 return Response({'product': product_serializer.data}, status=status.HTTP_200_OK)
#             else:
#                 products = Product.objects.all()
#                 product_serializer = ProductSerializer(products, many=True)
#                 return Response({'products': product_serializer.data},  status=status.HTTP_200_OK)

#         elif request.method == 'POST':
#             # Handle POST request to create a new product
#             new_product_data = {
#                 'name': request.data.get('name', ''),
#                 'product_code': request.data.get('product_code', ''),
#                 'product_rev_number': request.data.get('product_rev_number', ''),
#                 'project': project_id,


#                 # Add more fields as needed
#             }

#             try:
#                 # Create a new Product instance
#                 Product.objects.create(**new_product_data)

#                 # Return a success message
#                 return Response({'message': 'Product created successfully'}, status=status.HTTP_201_CREATED)
#             except Exception as e:
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     except Product.DoesNotExist:
#         return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_product(request, project_id):
    try:
        # Handle POST request to create a new product
        new_product_data = {
            'name': request.data.get('name', ''),
            'product_code': request.data.get('product_code', ''),
            'product_rev_number': request.data.get('product_rev_number', ''),
        }

        # Get the Project instance based on project_id
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found for the specified project_id'}, status=status.HTTP_404_NOT_FOUND)

        # Assign the project instance to the new product
        new_product_data['project'] = project

        try:
            # Create a new Product instance
            product = Product.objects.create(
                **new_product_data, created_by=request.user, updated_by=request.user)

            product_serializer = ProductSerializer(product)

            # Return a success message
            return Response({'product': product_serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    # Handle deleting the product
    product.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

# @api_view(['GET', 'POST'])
# def create_product(request, product_id=None):
#     try:
#         if request.method == 'GET':
#             # Handle GET request to retrieve a specific product by ID
#             if product_id:
#                 try:
#                     product = Product.objects.get(id=product_id)
#                     product_serializer = ProductSerializer(product)
#                     return Response({'product': product_serializer.data}, status=status.HTTP_200_OK)
#                 except Product.DoesNotExist:
#                     return Response({'error': 'Product not found for the specified ID'}, status=status.HTTP_404_NOT_FOUND)
#             else:
#                 return Response({'error': 'Product ID is required for GET request'}, status=status.HTTP_400_BAD_REQUEST)

#         elif request.method == 'POST':
#             # Handle POST request to create a new product
#             new_product_data = {
#                 'name': request.data.get('name', ''),
#                 'product_code': request.data.get('product_code', ''),
#                 'product_rev_number': request.data.get('product_rev_number', ''),
#             }

#             # Check if product_id is provided in the request
#             if product_id:
#                 try:
#                     # Get the existing Product instance based on product_id
#                     existing_product = Product.objects.get(id=product_id)
#                     # Assign the project instance from the existing product to the new product
#                     new_product_data['project'] = existing_product.project
#                 except Product.DoesNotExist:
#                     return Response({'error': 'Product not found for the specified product_id'}, status=status.HTTP_404_NOT_FOUND)

#             try:
#                 # Create a new Product instance
#                 product = Product.objects.create(**new_product_data)

#                 product_serializer = ProductSerializer(product)

#                 # Return a success message
#                 return Response({'product': product_serializer.data}, status=status.HTTP_201_CREATED)
#             except Exception as e:
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     except Product.DoesNotExist:
#         return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     except Product.DoesNotExist:
#         return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_orders(request):
    try:
        if request.method == 'GET':
            orders = Order.objects.all().order_by('-created_at')
            active_checklist_setting = ChecklistSetting.objects.first()
            active_checklist_data = None

            if active_checklist_setting:
                active_checklist = active_checklist_setting.active_checklist
                if active_checklist:
                    active_checklist_serializer = ChecklistWithoutItemsSerializer(
                        active_checklist)
                    active_checklist_data = active_checklist_serializer.data

            serializer = OrderListSerializer(orders, many=True)
            return Response({'orders': serializer.data, 'active_checklist': active_checklist_data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_projects(request):
    try:
        if request.method == 'GET':
            projects = Project.objects.all()
            serializer = ProjectSerializer(projects, many=True)
            return Response({'projects': serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Define the email sending function


@api_view(['GET', 'POST'])
def create_order(request, *args, **kwargs):
    try:
        # Fetch projects
        if request.method == 'GET':
            projects = Project.objects.all()
            project_serializer = ProjectSerializer(projects, many=True)

            # Fetch products (if project_id is provided)
            project_id = request.query_params.get('project_id')
            print("Project ID:", project_id)

            products = Product.objects.filter(
                project_id=project_id) if project_id else Product.objects.all()
            serialized_products = ProductSerializer(products, many=True).data

            # Fetch Bill of Materials without line items
            boms_without_line_items = BillOfMaterials.objects.all()
            bom_serializer = BillOfMaterialsListSerializer(
                boms_without_line_items, many=True)

            # Fetch Bill of Materials (BOMs) based on project_id
            # boms_by_project = BillOfMaterials.objects.filter(
            #     product__project_id=project_id)
            # bom_by_project_serializer = BillOfMaterialsListSerializer(
            #     boms_by_project, many=True)

            # Return all data in a single response
            bom_formats = BomFormat.objects.all()
            bom_formats_serializer = BomFormatSerializer(
                bom_formats, many=True)
            response_data = {
                'projects': project_serializer.data,
                'products': serialized_products,
                'boms': bom_serializer.data,
                'bom_formats': bom_formats_serializer.data
                # 'boms_by_project': bom_by_project_serializer.data,

            }

            return Response(response_data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
          # Extract data from the request
            selected_bom_id = request.data.get('selectedBomId')
            batch_quantity = request.data.get('batchQuantity')

            bom = BillOfMaterials.objects.get(id=selected_bom_id)

            # Create a new Order instance with the retrieved BillOfMaterials
            order = Order.objects.create(
                bom=bom, batch_quantity=batch_quantity, created_by=request.user, updated_by=request.user)

            # subject = 'New Order Notification'
            # message = f'A new order has been created.\n\nOrder Details:\nBOM: {bom}\nBatch Quantity: {batch_quantity}'
            # recipient_list = ['team_member1@example.com',
            #                   'team_member2@example.com']
            store_team_profiles = UserAccount.objects.filter(
                is_store_team=True)

            # Serialize the queryset using a serializer
            store_team_profiles_serializer = UserAccountSerializer(
                store_team_profiles, many=True).data
            print(store_team_profiles_serializer)
            send_order_creation_mail.delay(
                order.id, store_team_profiles_serializer)


# You can perform additional actions if needed

            # Return a success response
            return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    # Handle deleting the order
    order.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def create_order_task(request):
    # try:
    bom_file = request.FILES.get('bom_file')

    pcb_file = request.FILES.get('pcb_file')
    print('this is pcb file', pcb_file)

    bom_file_name = str(request.FILES['bom_file'].name)
    if bom_file is None:
        return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

    media_directory = os.path.join('bom_files', bom_file_name)

    bom_file_path = os.path.join(settings.MEDIA_ROOT, media_directory)

    os.makedirs(os.path.dirname(bom_file_path), exist_ok=True)

    with open(bom_file_path, 'wb') as destination:
        for chunk in bom_file.chunks():
            destination.write(chunk)

    bom_path = str(bom_file_path)
    print(bom_path)

    pcb_file_name = None
    pcb_path = None
    if pcb_file:
        pcb_file_name = str(request.FILES['pcb_file'].name)
        pcb_media_directory = os.path.join(
            'pcb_bbt_test_report_files', pcb_file_name)
        pcb_file_path = os.path.join(settings.MEDIA_ROOT, pcb_media_directory)
        os.makedirs(os.path.dirname(pcb_file_path), exist_ok=True)
        with open(pcb_file_path, 'wb') as destination:
            for chunk in pcb_file.chunks():
                destination.write(chunk)
        pcb_path = str(pcb_file_path)

    bom_data = {
        # 'product_name': request.data.get('product_name'),
        # 'product_code': request.data.get('product_code'),
        # 'product_rev_no': request.data.get('product_rev_no'),
        'project_id': request.data.get('project_id'),
        'product_id': request.data.get('product_id'),
        'bom_type': request.data.get('bom_type'),
        'bom_rev_no': request.data.get('bom_rev_no'),
        'issue_date': request.data.get('issue_date'),
        'bom_rev_change_note': request.data.get('bom_rev_change_note'),
        'batch_quantity': request.data.get('batch_quantity'),
        'bom_format_id': request.data.get('bom_format_id'),
        'pcb_file_name': pcb_file_name,
        'pcb_file_path': pcb_path,

    }
    print('project_id=', bom_data.get('project_id'))
    print('batch quantity=', bom_data.get('batch_quantity'))
    res = process_bom_file_and_create_order_new.delay(
        bom_path, bom_file_name, bom_data, request.user.id)
    task_result = AsyncResult(res.id)
    task_status = task_result.status
    print(task_status)
    print(task_result)
    return Response({'message': 'BOM upload task is queued for processing', 'task_id': res.id, 'task_status': str(task_status)}, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def upload_iqc_file(request):
    try:
        # Assuming 'iqc_file' is the key for the file in the FormData
        uploaded_file = request.FILES['iqc_file']

        # Assuming you have a ChecklistItemUID instance to associate the file with
        checklist_item_uid_id = request.data.get('checklist_item_uid_id')
        checklist_item_uid = ChecklistItemUID.objects.get(
            id=checklist_item_uid_id)

        # Assign the file to the 'iqc_file' field in your model
        checklist_item_uid.iqc_file = uploaded_file
        checklist_item_uid.save()

        return Response({'message': 'File uploaded successfully'}, status=status.HTTP_200_OK)

    except ChecklistItemUID.DoesNotExist:
        return Response({'error': 'ChecklistItemUID not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# @authentication_classes([])
# @permission_classes([])
# @api_view(['POST'])
# def upload_new_bom(request):
#     try:
#         # Assuming 'user' is defined somewhere in your code

#         # Get the uploaded file from the request
#         user = request.user
#         bom_file = request.FILES.get('bom_file')
#         bom_file_name = str(bom_file.name)

#         if bom_file is None:
#             return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

#         media_directory = os.path.join('bom_files', bom_file_name)
#         bom_file_path = os.path.join(settings.MEDIA_ROOT, media_directory)

#         os.makedirs(os.path.dirname(bom_file_path), exist_ok=True)

#         with open(bom_file_path, 'wb') as destination:
#             for chunk in bom_file.chunks():
#                 destination.write(chunk)

#         # Read the Excel file directly from the file object
#         bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

#         product = Product.objects.get(id=request.data.get('product_id'))

#         bom_type, _ = BillOfMaterialsType.objects.get_or_create(
#             name=request.data.get('bom_type'),
#             defaults={
#                 'updated_by': user,
#                 'created_by': user,
#             })

#         if (str(request.data.get('issue_date')) == ''):
#             issue_date = timezone.now().date()
#         else:
#             issue_date = request.data.get('issue_date')

#         bom, _ = BillOfMaterials.objects.get_or_create(
#             product=product,
#             issue_date=issue_date,
#             bom_file_name=bom_file_name,

#             defaults={
#                 'bom_type': bom_type,
#                 'bom_rev_number': request.data.get('bom_rev_no'),
#                 'change_note': request.data.get('bom_rev_change_note'),
#                 'bom_file': 'bom_files/' + bom_file_name,
#                 'updated_by': user,
#                 'created_by': user,
#             })

#         # Drop rows where 'vepl part' is NaN
#         bom_file_data = bom_file_data.dropna(subset=['VEPL Part No'])
#         bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
#             'VEPL')]

#         # Reset index after dropping rows
#         bom_file_data.reset_index(drop=True, inplace=True)

#         # Forward fill
#         bom_file_data.ffill(inplace=True)

#         # Lists to store instances and mapping
#         bom_line_items_to_create = []
#         vepl_to_references_mapping = {}
#         vepl_to_manufacturer_mapping = {}
#         processed_part_numbers = set()

#         # Iterate through rows in the DataFrame
#         for _, row in bom_file_data.head(7).iterrows():
#             print('index', _)
#             if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
#                 vepl_part_no = row['VEPL Part No']
#                 # Handling 'Mfr' field
#                 if pd.notnull(row['Mfr']):
#                     mfr_name = str(row.get('Mfr')).strip().replace('\n', '')
#                     manufacturer, _ = Manufacturer.objects.get_or_create(
#                         name=mfr_name,
#                         defaults={
#                             'updated_by': user,
#                             'created_by': user,
#                             # Add other fields if needed
#                         })
#                 else:
#                     manufacturer = None

#                 if pd.notnull(row['Mfr. Part No']):
#                     mfr_part_no = str(row.get('Mfr. Part No')
#                                       ).strip().replace('\n', '')
#                     manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
#                         part_number=mfr_part_no,
#                         manufacturer=manufacturer,
#                         defaults={
#                             'updated_by': user,
#                             'created_by': user,

#                         })
#                 else:
#                     manufacturer_part = None

#                 if vepl_part_no not in vepl_to_manufacturer_mapping:
#                     vepl_to_manufacturer_mapping[vepl_part_no] = []

#                 vepl_to_manufacturer_mapping[vepl_part_no].append(
#                     manufacturer_part)

#                 # Handling 'Reference' field
#                 if 'Reference' in row and pd.notnull(row['Reference']):
#                     for reference in str(row['Reference']).split(','):
#                         ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
#                             name=str(reference).strip(),
#                             defaults={
#                                 'updated_by': user,
#                                 'created_by': user,
#                             }
#                         )

#                         if vepl_part_no not in vepl_to_references_mapping:
#                             vepl_to_references_mapping[vepl_part_no] = []

#                         vepl_to_references_mapping[vepl_part_no].append(
#                             ref.name)
#                         print('vepl_to_references_mapping in loop',
#                               vepl_to_references_mapping)

#                 assembly_stage, _ = AssemblyStage.objects.get_or_create(
#                     name=row.get('Assy Stage', None),
#                     defaults={
#                         'updated_by': user,
#                         'created_by': user,
#                     })
#                 line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
#                     name=str(row.get('Type')).strip().upper(),
#                     defaults={
#                         'updated_by': user,
#                         'created_by': user,
#                     })

#                 checklist_item_type_value = ''
#                 if (row.get('Type')):
#                     if str(row.get('Type')).strip().upper() == 'PCB':
#                         checklist_item_type_value = 'PCB'
#                     elif str(row.get('Type')).strip().upper() == 'PCB SERIAL NUMBER LABEL':
#                         checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
#                     elif str(row.get('Type')).strip().upper() == 'SOLDER PASTE':
#                         checklist_item_type_value = 'SOLDER PASTE'
#                     elif str(row.get('Type')).strip().upper() == 'SOLDER BAR':
#                         checklist_item_type_value = 'SOLDER BAR'
#                     elif str(row.get('Type')).strip().upper() == 'IPA':
#                         checklist_item_type_value = 'IPA'
#                     elif str(row.get('Type')).strip().upper() == 'SOLDER FLUX':
#                         checklist_item_type_value = 'SOLDER FLUX'
#                     elif str(row.get('Type')).strip().upper() == 'SOLDER WIRE':
#                         checklist_item_type_value = 'SOLDER WIRE'
#                     elif str(row.get('Type')).strip().upper() == 'SMT PALLET':
#                         checklist_item_type_value = 'SMT PALLET'
#                     elif str(row.get('Type')).strip().upper() == 'WAVE PALLET':
#                         checklist_item_type_value = 'WAVE PALLET'
#                     else:
#                         checklist_item_type_value = 'RAW MATERIAL'

#                 checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
#                     'updated_by': user,
#                     'created_by': user,
#                 })

#                 level = row['Level'] if 'Level' in row and pd.notnull(
#                     row['Level']) else ''
#                 priority_level = row.get('Prioprity Level') if 'Prioprity Level' in row and pd.notnull(
#                     row['Prioprity Level']) else \
#                     row.get('Priority Level') if 'Priority Level' in row and pd.notnull(
#                         row['Priority Level']) else ''
#                 value = row['Value'] if 'Value' in row and pd.notnull(
#                     row['Value']) else ''
#                 pcb_footprint = row['PCB Footprint'] if 'PCB Footprint' in row and pd.notnull(
#                     row['PCB Footprint']) else ''
#                 description = row['Description'] if 'Description' in row and pd.notnull(
#                     row['Description']) else ''
#                 customer_part_number = row['Customer Part No'] if 'Customer Part No' in row and pd.notnull(
#                     row['Customer Part No']) else ''
#                 quantity = row['Qty/ Product'] if 'Qty/ Product' in row and pd.notnull(
#                     row['Qty/ Product']) else 0
#                 uom = row['UOM'] if 'UOM' in row and pd.notnull(
#                     row['UOM']) else ''
#                 ecn = row['ECN'] if 'ECN' in row and pd.notnull(
#                     row['ECN']) else ''
#                 msl = row['MSL'] if 'MSL' in row and pd.notnull(
#                     row['MSL']) else ''
#                 remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
#                     row['Remarks']) else ''

#                 existing_item = BillOfMaterialsLineItem.objects.filter(
#                     part_number=row['VEPL Part No'], bom=bom).first()

#                 if existing_item:
#                     existing_item.level = level
#                     existing_item.priority_level = priority_level
#                     existing_item.value = value
#                     existing_item.pcb_footprint = pcb_footprint
#                     existing_item.line_item_type = line_item_type
#                     existing_item.description = description
#                     existing_item.customer_part_number = customer_part_number
#                     existing_item.quantity = quantity
#                     existing_item.remarks = remarks
#                     existing_item.uom = uom
#                     existing_item.ecn = ecn
#                     existing_item.msl = msl
#                     existing_item.assembly_stage = assembly_stage
#                     existing_item.updated_by = user
#                     existing_item.created_by = user

#                     if existing_item.part_number in vepl_to_references_mapping:
#                         reference = BillOfMaterialsLineItemReference.objects.filter(
#                             name=vepl_to_references_mapping[vepl_part_no]).first()
#                         reference.bom_line_item = existing_item
#                         reference.save()
#                     if existing_item.part_number in vepl_to_manufacturer_mapping:
#                         existing_item.manufacturer_parts.set(
#                             vepl_to_manufacturer_mapping[vepl_part_no])
#                     existing_item.save()

#                 else:

#                     # Other fields handling...
#                     # Create BillOfMaterialsLineItem instance
#                     bom_line_item = BillOfMaterialsLineItem(
#                         part_number=row['VEPL Part No'],
#                         bom=bom,
#                         level=level,
#                         priority_level=priority_level,
#                         value=value,
#                         pcb_footprint=pcb_footprint,
#                         line_item_type=line_item_type,
#                         description=description,
#                         customer_part_number=customer_part_number,
#                         quantity=quantity,
#                         remarks=remarks,
#                         uom=uom,
#                         ecn=ecn,
#                         msl=msl,
#                         assembly_stage=assembly_stage,
#                         created_by=user,
#                         updated_by=user
#                     )
#                     bom_line_items_to_create.append(bom_line_item)
#                     dupli_count = 0
#                     for bom_line_item in bom_line_items_to_create:
#                         if bom_line_item.part_number == row['VEPL Part No']:
#                             dupli_count += 1
#                             print(str(bom_line_item.part_number) + 'exists')
#                     if dupli_count > 1:
#                         print('dupli count exceeded')
#                         bom_line_items_to_create.remove(bom_line_item)

#         BillOfMaterialsLineItem.objects.bulk_create(bom_line_items_to_create)

#         bom_line_items = BillOfMaterialsLineItem.objects.filter(bom=bom)
#         for bom_line_item in bom_line_items:
#             vepl_part_no = bom_line_item.part_number
#             if vepl_part_no in vepl_to_manufacturer_mapping:
#                 bom_line_item.manufacturer_parts.set(
#                     vepl_to_manufacturer_mapping[vepl_part_no])
#                 bom_line_item.save()
#             print('final',vepl_to_references_mapping)
#             if vepl_part_no in vepl_to_references_mapping:
#                 for ref in set(vepl_to_references_mapping[vepl_part_no]):
#                     print('current ref in loop ' , ref)
#                     reference = BillOfMaterialsLineItemReference.objects.filter(
#                         name=ref).first()
#                     if reference:
#                         print('got ref ', reference)
#                         if reference:
#                             reference.bom_line_item = bom_line_item
#                             reference.save()
#                             print('saved ref ', reference)

#         return Response({'message': 'Bom Uploaded successfully.'}, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# def send_order_creation_mail():

#     subject = 'Course Enrollment Notification'
#     context = {
#         # 'user_f_name': profile.first_name,
#         # 'user_l_name': profile.last_name,
#         # 'user_email': profile.user,
#         # 'course_title': course.title,
#     }
#     html_message = render_to_string('order_creation_mail.html', context)
#     plain_message = strip_tags(html_message)
#     sender_email = settings.EMAIL_HOST_USER
#     sender_name = 'Trainotel'
#     email_from = f'{sender_name} <{sender_email}>'
#     # test_email = 'sharmaps112000@gmail.com'
#     # recipient_list = [test_email]
#     recipient_list = [profile.user]
#     send_mail(subject, plain_message, email_from,
#               recipient_list, html_message=html_message)

# @api_view(['POST'])
# @authentication_classes([])
# @permission_classes([])
# def toggle_checklist_settings(request, checklist_id):
#     # Get the checklist object using the provided checklist_id
#     checklist = get_object_or_404(Checklist, id=checklist_id)

#     try:
#         # Get the checklist setting object if available, otherwise return a 404 error
#         checklist_setting = ChecklistSetting.objects.first()

#         if checklist_setting.active_checklist == checklist:
#             # If the active checklist matches the provided checklist, it means the checklist is active. In this case, pause the checklist.
#             checklist_setting.active_bom = None
#             checklist_setting.active_checklist = None
#             checklist.status = 'Paused'  # Update the status to 'Paused'
#             checklist.save()
#             message = 'Checklist has been paused successfully.'
#             status_code = 200  # OK
#         else:
#             # Check if there's another checklist in progress
#             active_checklist_setting = ChecklistSetting.objects.first()
#             active_checklist = active_checklist_setting.active_checklist
#             active_bom = active_checklist_setting.active_bom
#             if active_checklist and active_bom:
#                 # Pause the currently active checklist
#                 # Set the active checklist to None
#                 active_checklist_setting.active_checklist = None
#                 active_checklist_setting.active_bom = None
#                 active_checklist.status = 'Paused'
#                 active_checklist.save()

#             # Resume the provided checklist
#             checklist_setting.active_bom = checklist.bom
#             checklist_setting.active_checklist = checklist
#             checklist.status = 'In Progress'  # Update the status to 'In Progress'
#             checklist.save()
#             message = 'Checklist has been resumed successfully.'
#             status_code = 200  # OK

#         checklist_setting.save()

#         return JsonResponse({'message': message}, status=status_code)
#     except Exception as e:
#         # If any error occurs, return a JSON response with a 500 status code and the error message
#         return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def pause_checklist(request, checklist_id):
    # Get the checklist object using the provided checklist_id
    checklist = get_object_or_404(Checklist, id=checklist_id)

    try:
        # Retrieve the first ChecklistSetting object
        checklist_setting = ChecklistSetting.objects.first()
        if checklist_setting.active_checklist == checklist:

            # Pause the provided checklist
            checklist_setting.active_bom = None
            checklist_setting.active_checklist = None
            checklist.status = 'Paused'
            checklist.save()
            checklist_setting.save()

            message = 'Checklist has been paused successfully.'
            return Response({'message': message}, status=status.HTTP_200_OK)
        else:
            # If the active checklist doesn't match the provided checklist, return a mismatch message
            return Response({'error': 'Mismatch: The provided checklist is not the active checklist.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # If any error occurs, return a JSON response with a 500 status code and the error message
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def resume_checklist(request, checklist_id):
    # Get the checklist object using the provided checklist_id
    checklist = get_object_or_404(Checklist, id=checklist_id)

    try:
        # Retrieve the ChecklistSetting object
        checklist_setting = ChecklistSetting.objects.first()

        if checklist_setting:
            # Get the currently active checklist from the ChecklistSetting
            active_checklist = checklist_setting.active_checklist

            # If there's another active checklist, pause it
            if active_checklist and active_checklist != checklist:
                active_checklist.status = 'Paused'
                active_checklist.save()

            # Update the provided checklist to be active and set its status to 'In Progress'
            checklist.status = 'In Progress'
            checklist.save()

            # Update the active checklist in the ChecklistSetting
            checklist_setting.active_checklist = checklist
            checklist_setting.active_bom = checklist.bom
            checklist_setting.save()

            message = 'Checklist has been resumed successfully.'
            return Response({'message': message}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No ChecklistSetting instance found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_inspection_board_data(request, inspection_board_id):
    try:
        inspection_board = InspectionBoard.objects.get(pk=inspection_board_id)
        serializer = InspectionBoardDetailedSerializer(inspection_board)
        defect_types = DefectType.objects.all()
        defect_types_serializer = DefectTypeSerializer(defect_types, many=True)

        return Response({'inspectionBoardData': serializer.data, 'defectTypes': defect_types_serializer.data})
    except InspectionBoard.DoesNotExist:
        return Response(status=404)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def assign_defect_type(request):
    if request.method == 'POST':
        defect_id = request.data.get('defect_id')
        print('defect_id', defect_id)
        defect_type_id = request.data.get('defect_type_id')
        print('defect_type_id', defect_type_id)
        board_id = request.data.get('board_id')
        print('board_id', board_id)

        # Retrieve the defect object
        try:
            defect = Defect.objects.get(pk=defect_id)
        except Defect.DoesNotExist:
            return Response({'error': 'Defect not found.'}, status=400)

        # Retrieve the defect type object
        try:
            defect_type = DefectType.objects.get(id=defect_type_id)
        except DefectType.DoesNotExist:
            return Response({'error': 'Defect type not found.'}, status=400)

        # Assign defect type to defect
        defect.defect_type = defect_type
        defect.save()

        # Retrieve the inspection board object based on board_id
        try:
            inspection_board = InspectionBoard.objects.get(id=board_id)
        except InspectionBoard.DoesNotExist:
            return Response({'error': 'Inspection board not found.'}, status=400)

        # Serialize the inspection board object
        serializer = InspectionBoardDetailedSerializer(inspection_board)
        defect_types = DefectType.objects.all()
        defect_types_serializer = DefectTypeSerializer(defect_types, many=True)

        # Return serialized inspection board data
    return Response({'inspectionBoardData': serializer.data, 'defectTypes': defect_types_serializer.data})

    return Response({'error': 'Invalid request method.'}, status=405)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_defect_type(request):
    if request.method == 'POST':
        name = request.data.get('defectName')

        # Create a new defect type object
        defect_type = DefectType.objects.create(
            name=name)
        # Serialize the new defect type object

        defect_types = DefectType.objects.all()

        defect_types_serializer = DefectTypeSerializer(defect_types, many=True)

        # Return serialized defect type data
        return Response({'message': 'Defect Type created successfully', 'defectTypes': defect_types_serializer.data}, status=201)

    return Response({'error': 'Invalid request method.'}, status=405)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_inspection_boards(request):
    if request.method == 'GET':
        inspection_boards = InspectionBoard.objects.all()

        checklist_settings = ChecklistSetting.objects.first()
        active_inspection_board = checklist_settings.active_inspection_board
        active_inspection_board_data = None
        if active_inspection_board:
            active_inspection_board_serializer = InspectionBoardSerializer(
                active_inspection_board)
            active_inspection_board_data = active_inspection_board_serializer.data

        serializer = InspectionBoardSerializer(inspection_boards, many=True)
        return JsonResponse({'inspectionBoards': serializer.data, 'activeInspectionBoard': active_inspection_board_data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_inspection_board(request):
    if request.method == 'POST':
        # Extract data from the request
        detected_board_id = request.POST.get('detected_board_id', None)
        board_name = request.POST.get('board_name', '')
        board_image = request.FILES.get('board_image', None)

        # Check if required fields are provided
        if detected_board_id is None or board_image is None:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Create the inspection board instance
        new_inspection_board = InspectionBoard(
            detected_board_id=detected_board_id,
            name=board_name,
            inspection_board_image=board_image
        )

        # Save the inspection board instance
        new_inspection_board.save()

        # Set the new inspection board as the active_inspection_board in ChecklistSetting
        # Assuming there's only one ChecklistSetting instance
        checklist_setting = ChecklistSetting.objects.first()
        if checklist_setting:
            checklist_setting.active_inspection_board = new_inspection_board
            checklist_setting.save()

        try:
            # Serialize the active inspection board
            active_inspection_board = checklist_setting.active_inspection_board
            active_inspection_board_serialized = InspectionBoardSerializer(
                active_inspection_board)

            # active_inspection_board_serialized = InspectionBoardSerializer(new_inspection_board)

            # Serialize the list of all inspection boards
            inspection_boards = InspectionBoard.objects.all()
            inspection_boards_serialized = InspectionBoardSerializer(
                inspection_boards, many=True)

            # Send data through channels
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'inspection_board_create_group',  # Group name defined in your WebSocket consumer
                {
                    # Method name defined in your WebSocket consumer
                    'type': 'send_inspection_board',
                    'active_inspection_board': active_inspection_board_serialized.data,
                    'all_inspection_boards': inspection_boards_serialized.data
                }
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return success response
        return JsonResponse({'message': 'Inspection board created successfully'}, status=201)

    else:
        # Return error response for unsupported methods
        return JsonResponse({'error': 'Method not allowed'}, status=405)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def add_defects_to_board(request):

    if request.method == 'POST':
        # Get data from request payload
        detected_board_id = request.data.get('detected_board_id')
        defect_images = request.FILES.getlist('defect_images')

        # Check if all required fields are present in the request
        if not detected_board_id or not defect_images:
            return Response({'error': 'One or more required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the InspectionBoard instance
        try:
            board = InspectionBoard.objects.get(
                detected_board_id=detected_board_id)
        except InspectionBoard.DoesNotExist:
            return Response({'error': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create defects and associate them with the board
        for defect_image in defect_images:
            defect = Defect.objects.create(
                inspection_board=board,
                defect_image=defect_image
            )

        return Response({'message': 'Defects added successfully'}, status=status.HTTP_201_CREATED)
    else:
        return Response({'error': 'Only POST requests are allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def assign_defect_to_board(request):
    if request.method == 'POST':
        try:
            # Get data from request payload
            detected_board_id = request.data.get('detected_board_id')
            defect_image_id = request.data.get('defect_image_id')
            defect_image_file = request.FILES.get('defect_image')
            # defect_image_id = request.data.get(
            #     'defect_image', {}).get('defect_image_id')
            # defect_image_file = request.data.get(
            #     'defect_image', {}).get('defect_image')

            # Check if all required fields are present in the request
            if not detected_board_id or not defect_image_id or not defect_image_file:
                return Response({'error': 'One or more required fields are missing'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the InspectionBoard instance
            try:
                board = InspectionBoard.objects.get(
                    detected_board_id=detected_board_id)
            except InspectionBoard.DoesNotExist:
                return Response({'error': 'Board not found'}, status=status.HTTP_404_NOT_FOUND)

            # Check if a defect with the same defect_image_id already exists
            existing_defect = Defect.objects.filter(
                defect_image_id=defect_image_id).first()
            if existing_defect:
                return Response({'error': 'Defect with the same image ID already exists'}, status=status.HTTP_400_BAD_REQUEST)

            # Create the defect and associate it with the board
            defect = Defect.objects.create(
                inspection_board=board,
                defect_image=defect_image_file,
                defect_image_id=defect_image_id
            )

            return Response({'message': 'Defect assigned to board successfully'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Only POST requests are allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# @api_view(['POST'])
# @authentication_classes([])
# @permission_classes([])
# def parse_bom_new(request):
#     try:
#         # Get BOM ID from request data
#         bom_id = request.data.get('bom_id')
#         bom = get_object_or_404(BillOfMaterials, id=bom_id)

#         # Get the uploaded file
#         file = request.FILES['file']
#         excel_data = pd.read_excel(
#             BytesIO(file.read()), sheet_name='gen2_1600w_aux_supply', header=11)

#         # Replace NaN values with None in the Excel data

#         # Rename columns to match the expected format
#         excel_data.columns = [
#             "Level", "VEPL Part No", "Priority Level", "Value", "PCB Footprint",
#             "Type", "Description", "Mfr", "Mfr. Part No", "Customer Part No",
#             "Qty", "Reference"
#         ]

#         for index, row in excel_data.iterrows():
#             # Check if 'Mfr. Part No' is not None
#             mfr_part_number = row['Mfr. Part No'] if pd.notna(
#                 row['Mfr. Part No']) else None
#             if mfr_part_number is not None:
#                 # Update or create Manufacturer
#                 manufacturer_name = row['Mfr'] if pd.notna(
#                     row['Mfr']) else None
#                 manufacturer, created = Manufacturer.objects.update_or_create(
#                     name=manufacturer_name,
#                     # Specify default values here if necessary
#                     defaults={} if manufacturer_name is not None else None
#                 )
#                 print(
#                     f"Manufacturer {'updated' if not created else 'created'}: {manufacturer}")

#                 # Create or get ManufacturerPart
#                 mfr_part, updated = ManufacturerPart.objects.update_or_create(
#                     part_number=mfr_part_number,
#                     manufacturer=manufacturer if manufacturer_name is not None else None
#                 )
#                 print(
#                     f"ManufacturerPart {'updated' if not updated else 'created'}: {mfr_part}")

#                 # Create or get BillOfMaterialsLineItemType
#                 line_item_type_name = row['Type'] if pd.notna(
#                     row['Type']) else None
#                 line_item_type, created = BillOfMaterialsLineItemType.objects.update_or_create(
#                     name=line_item_type_name,
#                     # Specify default values here if necessary
#                     defaults={} if line_item_type_name is not None else None
#                 )
#                 print(
#                     f"BillOfMaterialsLineItemType {'updated' if not created else 'created'}: {line_item_type}")

#                 existing_bom_line_item = BillOfMaterialsLineItem.objects.filter(
#                     bom=bom,
#                     manufacturer_parts=mfr_part
#                 ).first()

#                 # Create or update BOM Line Item
#                 if existing_bom_line_item:
#                     # ManufacturerPart exists for this BOM Line Item, so update it
#                     bom_line_item = existing_bom_line_item
#                     bom_line_item.level = row['Level'] if pd.notna(
#                         row['Level']) else None
#                     bom_line_item.priority_level = row['Priority Level'] if pd.notna(
#                         row['Priority Level']) else None
#                     bom_line_item.value = row['Value'] if pd.notna(
#                         row['Value']) else None
#                     bom_line_item.pcb_footprint = row['PCB Footprint'] if pd.notna(
#                         row['PCB Footprint']) else None
#                     bom_line_item.line_item_type = line_item_type
#                     bom_line_item.description = row['Description'] if pd.notna(
#                         row['Description']) else None
#                     bom_line_item.customer_part_number = row['Customer Part No'] if pd.notna(
#                         row['Customer Part No']) else None
#                     bom_line_item.quantity = int(
#                         row['Qty']) if pd.notna(row['Qty']) else 0
#                     bom_line_item.save()
#                     print(f"BOM Line Item updated: {bom_line_item}")
#                 else:
#                     # ManufacturerPart doesn't exist for this BOM Line Item, so create it
#                     bom_line_item = BillOfMaterialsLineItem.objects.create(
#                         bom=bom,
#                         level=row['Level'] if pd.notna(row['Level']) else None,
#                         priority_level=row['Priority Level'] if pd.notna(
#                             row['Priority Level']) else None,
#                         value=row['Value'] if pd.notna(row['Value']) else None,
#                         pcb_footprint=row['PCB Footprint'] if pd.notna(
#                             row['PCB Footprint']) else None,
#                         line_item_type=line_item_type,
#                         description=row['Description'] if pd.notna(
#                             row['Description']) else None,
#                         customer_part_number=row['Customer Part No'] if pd.notna(
#                             row['Customer Part No']) else None,
#                         quantity=int(row['Qty']) if pd.notna(
#                             row['Qty']) else 0,
#                     )
#                     # Add ManufacturerPart to the many-to-many relationship
#                     bom_line_item.manufacturer_parts.add(mfr_part)
#                     print(f"BOM Line Item created: {bom_line_item}")

#                 # Update or create BillOfMaterialsLineItemReference instances
#                 references = row['Reference']
#                 if references is not None:
#                     for reference in str(references).split(','):
#                         ref, _ = BillOfMaterialsLineItemReference.objects.update_or_create(
#                             name=str(reference).strip(),
#                             bom_line_item=bom_line_item,  # Include the BillOfMaterialsLineItem reference
#                             defaults={
#                                 # 'updated_by': request.user,
#                                 # 'created_by': request.user,
#                             }
#                         )
#                         # print(f"BillOfMaterialsLineItemReference {'updated' if not _ else 'created'}: {ref}")

#         return Response({"status": "success", "message": "BOM line items parsed and saved successfully."})
#     except Exception as e:
#         return Response({"status": "error", "message": str(e)})
