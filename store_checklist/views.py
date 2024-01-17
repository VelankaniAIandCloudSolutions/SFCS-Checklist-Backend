
from .serializers import BillOfMaterialsLineItemSerializer, ManufacturerPartSerializer, BillOfMaterialsLineItemReferenceSerializer, BillOfMaterialsLineItemTypeSerializer
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
from .tasks import process_bom_file, test_func, process_bom_file_and_create_order
import os
from django.conf import settings
from celery.result import AsyncResult


@api_view(['POST'])
def upload_bom_task(request):
    # try:
    bom_file = request.FILES.get('bom_file')
    bom_file_name = str(request.FILES['bom_file'].name)
    if bom_file is None:
        return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

    media_directory = os.path.join('bom_files', bom_file_name)

    bom_file_path = os.path.join(settings.MEDIA_ROOT, media_directory)

    os.makedirs(os.path.dirname(bom_file_path), exist_ok=True)

    with open(bom_file_path, 'wb') as destination:
        for chunk in bom_file.chunks():
            destination.write(chunk)

    path = str(bom_file_path)

    bom_data = {
        'project_id': request.data.get('project_id'),
        'product_id': request.data.get('product_id'),
        'product_rev_no': request.data.get('product_rev_no'),
        'bom_type': request.data.get('bom_type'),
        'bom_rev_no': request.data.get('bom_rev_no'),
        'issue_date': request.data.get('issue_date'),
        'batch_quantity': request.data.get('batch_quantity'),
    }
    print('project_id=', bom_data.get('project_id'))
    print('batch quantity=', bom_data.get('batch_quantity'))
    res = process_bom_file.delay(
        path, bom_file_name, bom_data, request.user.id)
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


@authentication_classes([])
@permission_classes([])
def scan_code(request):

    print(request.data)
    # input_string = "u1UUID000128808-VEPL145154751D<Facts>Q500"
    # pattern = r'ue1([^\-]+)-(VEPL\d{8})'
    # match = re.search(pattern, request.data.get('value'))

    text = request.data.get('value')
    uid_pattern = r'.*?1U(.*?)-'
    vepl_pattern = r'(VEPL.*?)(?=1D<)'
    quantity_pattern = r'Q(\d+)'
    uid_match = re.search(uid_pattern, text)
    vepl_match = re.search(vepl_pattern, text)
    quantity_match = re.search(quantity_pattern, text)

    if quantity_match:
        quantity = int(quantity_match.group(1))
    else:
        quantity = 0

    if vepl_match:
        uuid = uid_match.group(1)
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

            if ChecklistItemUID.objects.filter(uid=uuid).exists():
                return JsonResponse({'message': f'UUID {uuid} already exists in ChecklistItemUID table'}, status=400)
            else:

                for bom_line_item in active_bom.bom_line_items.all():
                    print("BOM Line Item Part Number:",
                          bom_line_item.part_number.strip())
                    print("Input Part Number:", part_number.strip())

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

                        # if ChecklistItem.objects.filter(checklist = active_checklist, bom_line_item = bom_line_item).exists():
                        #     checklist_item.checklist_item_type = checklist_item_type
                        #     checklist_item.save()
                        #     checklist_item_created = False
                        # else:
                        #     ChecklistItem.objects.create(checklist = active_checklist, bom_line_item = bom_line_item,checklist_item_type = checklist_item_type)
                        #     checklist_item_created = True

                        checklist_item_uid, checklist_item_uid_created = ChecklistItemUID.objects.get_or_create(
                            checklist_item=checklist_item,
                            uid=uuid,
                            # defaults={
                            #     'updated_by': request.user,
                            #     'created_by': request.user,
                            # }

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

        return Response({
            'uuid': uuid,
            'part_number': part_number,
            'is_present': is_present,
            'is_quantity_sufficient': is_quantity_sufficient,

        })

    else:
        print("Pattern not found in the input string.")
        return Response({'error': 'Invalid input string'}, status=status.HTTP_400_BAD_REQUEST)


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
            print('doesnt exist')
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

        boms_without_line_items = BillOfMaterials.objects.all()
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

        checklist_serializer = ChecklistSerializer(checklist)
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
        checklists = Checklist.objects.filter(bom=bom)

        # Serialize the checklists using ChecklistSerializer
        serializer = ChecklistSerializer(checklists, many=True)

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
            updated_at__date__range=[start_date, end_date]
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
            'in_progress': ChecklistSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistSerializer(failed_checklists, many=True).data,
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
            'in_progress': ChecklistSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistSerializer(failed_checklists, many=True).data,
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
            'in_progress': ChecklistSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistSerializer(failed_checklists, many=True).data,
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
            'in_progress': ChecklistSerializer(in_progress_checklists, many=True).data,
            'completed_checklists': ChecklistSerializer(completed_checklists, many=True).data,
            'failed_checklists': ChecklistSerializer(failed_checklists, many=True).data,
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
                    name=reference_name, bom_line_item=bom_line_item
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
@authentication_classes([])
@permission_classes([])
def update_checklist_item(request, checklist_item_id):
    try:
        checklist_item = ChecklistItem.objects.get(id=checklist_item_id)
        present_quantity = int(request.data.get('present_quantity', 0))

        checklist_item.present_quantity = present_quantity

        checklist_item.is_present = checklist_item.present_quantity > 0
        checklist_item.is_quantity_sufficient = checklist_item.present_quantity >= checklist_item.required_quantity

        checklist_item.save()

        return Response({'message': 'Checklist item updated successfully'}, status=status.HTTP_200_OK)
    except ChecklistItem.DoesNotExist:
        return Response({'message': 'Checklist item not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({'message': 'Invalid present quantity'}, status=status.HTTP_400_BAD_REQUEST)


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
            'project_rev_number': request.data.get('project_rev_number', ''),
            # Add more fields as needed
        }

        # Create a new Project instance
        project = Project.objects.create(**project_data)

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
            product = Product.objects.create(**new_product_data)

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
            orders = Order.objects.all()
            serializer = OrderSerializer(orders, many=True)
            return Response({'orders': serializer.data}, status=status.HTTP_200_OK)
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
            response_data = {
                'projects': project_serializer.data,
                'products': serialized_products,
                'boms': bom_serializer.data,
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
                bom=bom, batch_quantity=batch_quantity)

            # You can perform additional actions if needed

            # Return a success response
            return Response({'message': 'Order created successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_order_task(request):
    # try:
    bom_file = request.FILES.get('bom_file')
    bom_file_name = str(request.FILES['bom_file'].name)
    if bom_file is None:
        return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

    media_directory = os.path.join('bom_files', bom_file_name)

    bom_file_path = os.path.join(settings.MEDIA_ROOT, media_directory)

    os.makedirs(os.path.dirname(bom_file_path), exist_ok=True)

    with open(bom_file_path, 'wb') as destination:
        for chunk in bom_file.chunks():
            destination.write(chunk)

    path = str(bom_file_path)
    print(path)
    bom_data = {
        # 'product_name': request.data.get('product_name'),
        # 'product_code': request.data.get('product_code'),
        # 'product_rev_no': request.data.get('product_rev_no'),
        'project_id': request.data.get('project_id'),
        'product_id': request.data.get('product_id'),
        'bom_type': request.data.get('bom_type'),
        'bom_rev_no': request.data.get('bom_rev_no'),
        'issue_date': request.data.get('issue_date'),
        'batch_quantity': request.data.get('batch_quantity'),

    }
    print('project_id=', bom_data.get('project_id'))
    print('batch quantity=', bom_data.get('batch_quantity'))
    res = process_bom_file_and_create_order.delay(
        path, bom_file_name, bom_data, request.user.id)
    task_result = AsyncResult(res.id)
    task_status = task_result.status
    print(task_status)
    print(task_result)
    return Response({'message': 'BOM upload task is queued for processing', 'task_id': res.id, 'task_status': str(task_status)}, status=status.HTTP_202_ACCEPTED)
