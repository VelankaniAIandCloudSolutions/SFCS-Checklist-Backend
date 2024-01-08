
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
from .tasks import test_func, process_bom_file
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
        'product_name': request.data.get('product_name'),
        'product_code': request.data.get('product_code'),
        'product_rev_no': request.data.get('product_rev_no'),
        'bom_type': request.data.get('bom_type'),
        'bom_rev_no': request.data.get('bom_rev_no'),
        'issue_date': request.data.get('issue_date'),
    }
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

# @api_view(['POST'])
# def upload_bom(request):
#     # if 'file' not in request.FILES:
#     #     return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

#     # try:
#     bom_file = request.FILES['bom_file']
#     bom_file_name = str(request.FILES['bom_file'].name)
#     # file_path  = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
#     data = pd.read_excel(bom_file, header=5, sheet_name=1)
#     product, _ = Product.objects.get_or_create(
#         name=request.data.get('product_name'),
#         product_code=request.data.get('product_code'),
#         defaults={
#             'product_rev_number': request.data.get('product_rev_no'),
#             'updated_by': request.user,
#             'created_by': request.user,
#         }
#     )
#     bom_type, _ = BillOfMaterialsType.objects.get_or_create(
#         name=request.data.get('bom_type'),
#         defaults={
#             'updated_by': request.user,
#             'created_by': request.user,
#         })

#     bom, _ = BillOfMaterials.objects.get_or_create(
#         product=product,
#         issue_date=request.data.get('issue_date'),
#         bom_file_name=bom_file_name,
#         defaults={
#             'bom_type': bom_type,
#             'bom_rev_number': request.data.get('bom_rev_no'),
#             'bom_file': bom_file,
#             'updated_by': request.user,
#             'created_by': request.user,
#         }
#     )
#     # bom  = BillOfMaterials.objects.all()[0]

#     for _, row in data.iterrows():
#         if  str(row['VEPL Part No'])!='nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
#             print(row)
#             assembly_stage, _ = AssemblyStage.objects.get_or_create(
#                 name=row.get('Assy Stage', None),
#                 defaults={
#                     'updated_by': request.user,
#                     'created_by': request.user,
#                 })
#             line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
#                 name=row.get('Type').strip().upper(),
#                 defaults={
#                     'updated_by': request.user,
#                     'created_by': request.user,
#                     })
#             checklist_item_type_value = ''
#             if(row.get('Type')):
#                 if row.get('Type').strip().upper() == 'PCB':
#                     checklist_item_type_value = 'PCB'
#                 elif row.get('Type').strip().upper() == 'PCB SERIAL NUMBER LABEL':
#                     checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
#                 elif row.get('Type').strip().upper() == 'SOLDER PASTE':
#                     checklist_item_type_value = 'SOLDER PASTE'
#                 elif row.get('Type').strip().upper() == 'SOLDER BAR':
#                     checklist_item_type_value = 'SOLDER BAR'
#                 elif row.get('Type').strip().upper() == 'IPA':
#                     checklist_item_type_value = 'IPA'
#                 elif row.get('Type').strip().upper() == 'SOLDER FLUX':
#                     checklist_item_type_value = 'SOLDER FLUX'
#                 elif row.get('Type').strip().upper() == 'SOLDER WIRE':
#                     checklist_item_type_value = 'SOLDER WIRE'
#                 elif row.get('Type').strip().upper() == 'SMT PALLET':
#                     checklist_item_type_value = 'SMT PALLET'
#                 elif row.get('Type').strip().upper() == 'WAVE PALLET':
#                     checklist_item_type_value = 'WAVE PALLET'
#                 else:
#                     checklist_item_type_value = 'RAW MATERIAL'

#             checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
#                 'updated_by': request.user,
#             'created_by': request.user,
#             })

#             level = row['Level'] if 'Level' in row and pd.notnull(
#                 row['Level']) else ''
#             priority_level = row.get('Prioprity Level') if 'Prioprity Level' in row and pd.notnull(row['Prioprity Level']) else \
#                 row.get('Priority Level') if 'Priority Level' in row and pd.notnull(
#                     row['Priority Level']) else ''
#             value = row['Value'] if 'Value' in row and pd.notnull(
#                 row['Value']) else ''
#             pcb_footprint = row['PCB Footprint'] if 'PCB Footprint' in row and pd.notnull(
#                 row['PCB Footprint']) else ''
#             description = row['Description'] if 'Description' in row and pd.notnull(
#                 row['Description']) else ''
#             customer_part_number = row['Customer Part No'] if 'Customer Part No' in row and pd.notnull(
#                 row['Customer Part No']) else ''
#             quantity = row['Qty/ Product'] if 'Qty/ Product' in row and pd.notnull(
#                 row['Qty/ Product']) else 0
#             uom = row['UOM'] if 'UOM' in row and pd.notnull(row['UOM']) else ''
#             ecn = row['ECN'] if 'ECN' in row and pd.notnull(row['ECN']) else ''
#             msl = row['MSL'] if 'MSL' in row and pd.notnull(row['MSL']) else ''
#             remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(row['Remarks']) else ''

#             bom_line_item, created = BillOfMaterialsLineItem.objects.update_or_create(
#                 part_number=row['VEPL Part No'],
#                 bom=bom,
#                 defaults={
#                     'level': level,
#                     'priority_level': priority_level,
#                     'value': value,
#                     'pcb_footprint': pcb_footprint,
#                     'line_item_type': line_item_type,
#                     'description': description,
#                     'customer_part_number': customer_part_number,
#                     'quantity': quantity,
#                     'remarks': remarks,
#                     'uom': uom,
#                     'ecn': ecn,
#                     'msl': msl,
#                     'assembly_stage': assembly_stage,
#                     'created_by': request.user,
#                     'updated_by': request.user,
#                 }
#             )

#             if pd.notnull(row['Mfr']):
#                 parts = [part.strip()
#                         for part in row['Mfr'].split('\n') if part.strip()]
#                 manufacturers = parts if not row['Mfr'].startswith(
#                     '\n') else parts[1:]
#             else:
#                 manufacturers = []

#             if pd.notnull(row['Mfr. Part No']):
#                 parts = [part.strip()
#                         for part in row['Mfr. Part No'].split('\n') if part.strip()]
#                 manufacturer_part_nos = parts if not row['Mfr. Part No'].startswith(
#                     '\n') else parts[1:]
#             else:
#                 manufacturer_part_nos = []

#             print('manufacturer parts', manufacturer_part_nos)

#             bom_line_item.manufacturer_parts.clear()
#             for mfr, mfr_part_no in zip(manufacturers, manufacturer_part_nos):
#                 if mfr.strip() and mfr_part_no.strip():
#                     manufacturer, _ = Manufacturer.objects.get_or_create(
#                         name=mfr.strip(),
#                         defaults={
#                             'updated_by': request.user,
#             'created_by': request.user,
#                         })
#                     manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
#                         part_number=mfr_part_no.strip(),
#                         manufacturer=manufacturer,
#                         defaults={
#                             'updated_by': request.user,
#             'created_by': request.user,
#                         }
#                     )

#                     bom_line_item.manufacturer_parts.add(manufacturer_part)
#             bom_line_item.save()

#             if 'Reference' in row and pd.notnull(row['Reference']):
#                 for reference in row['Reference'].split(','):
#                     ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
#                         name=reference.strip(),
#                         bom_line_item=bom_line_item,
#                         defaults={
#                             'updated_by': request.user,
#                             'created_by': request.user,
#                         }
#                     )

#             bom_items_serializer = BillOfMaterialsLineItemSerializer(
#                 bom.bom_line_items, many=True)

#     return Response({
#         'message': 'BOM uploaded successfully',
#         'bom_items': bom_items_serializer.data,
#     }, status=status.HTTP_201_CREATED)

#     # except Exception as e:
#     #     # Handle exceptions
#     #     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
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
def generate_new_checklist(request, bom_id):
    try:
        active_bom = BillOfMaterials.objects.get(id=bom_id)
        batch_quantity = request.data.get('batch_quantity') or 1
        if ChecklistSetting.objects.exists():
            setting = ChecklistSetting.objects.first()
            print('exists')
        else:
            setting = ChecklistSetting.objects.create(
                active_bom=BillOfMaterials.objects.get(id=bom_id), created_by=request.user, updated_by=request.user)
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
        boms = BillOfMaterials.objects.all()
        serializer = BillOfMaterialsSerializer(boms, many=True)

        return Response({'boms': serializer.data}, status=status.HTTP_200_OK)

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


@api_view(['GET'])
def get_projects(request):
    try:
        if request.method == 'GET':
            projects = Project.objects.all()
            project_serializer = ProjectSerializer(projects, many=True)
            return Response({'projects': project_serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_products_by_project(request, project_id):
    try:
        if request.method == 'GET':
            products = Product.objects.filter(project_id=project_id)
            serialized_products = ProductSerializer(products, many=True).data
            return Response({'products': serialized_products}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_orders(request):
    try:
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return JsonResponse({'orders': serializer.data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
