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

# @api_view(['GET'])
# @authentication_classes([])
# @permission_classes([])
# def test_api(request):

#     file_path = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
#     excel =  pd.read_excel(file_path,sheet_name=1)
#     print(excel.iloc[1])
#     print(excel.iloc[2])
#     print(excel.iloc[3])
#     print(excel.iloc[4])
#     excel_data = pd.read_excel(file_path, header=5,sheet_name=1).head(10)
#     # print(excel_data.columns.tolist())
#     data = excel_data.to_dict('records')
#     # for index, row in excel_data.iterrows():

#     #     print(row['VEPL Part No'])

#     return Response({
#         'data': json.dumps(data)
#     })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def upload_bom(request):
    # if 'file' not in request.FILES:
    #     return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

    # try:
    # Read the Excel file using pandas
    bom_file = request.FILES['bom_file']
    bom_file_name = str(request.FILES['bom_file'].name)
    # file_path  = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
    data = pd.read_excel(bom_file, header=5, sheet_name=1).head(10)
    product, _ = Product.objects.get_or_create(
        name=request.data.get('product_name'),
        product_code=request.data.get('product_code'),
        defaults={
            'product_rev_number': request.data.get('product_rev_no')
        }
    )
    bom_type, _ = BillOfMaterialsType.objects.get_or_create(
        name=request.data.get('bom_type'))

    bom, _ = BillOfMaterials.objects.get_or_create(
        product=product,
        issue_date=request.data.get('issue_date'),
        bom_file_name=bom_file_name,
        defaults={
            'bom_type': bom_type,
            'bom_rev_number': request.data.get('bom_rev_no'),
            'bom_file': bom_file,
        }
    )
    # bom  = BillOfMaterials.objects.all()[0]

    for _, row in data.iterrows():
        if row['VEPL Part No'] != '':
            print(row)
            assembly_stage, _ = AssemblyStage.objects.get_or_create(
                name=row.get('Assy Stage', None))
            line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
                name=row.get('Type', None))

            level = row['Level'] if 'Level' in row and pd.notnull(
                row['Level']) else ''
            priority_level = row.get('Prioprity Level') if 'Prioprity Level' in row and pd.notnull(row['Prioprity Level']) else \
                row.get('Priority Level') if 'Priority Level' in row and pd.notnull(
                    row['Priority Level']) else ''
            value = row['Value'] if 'Value' in row and pd.notnull(
                row['Value']) else ''
            pcb_footprint = row['PCB Footprint'] if 'PCB Footprint' in row and pd.notnull(
                row['PCB Footprint']) else ''
            description = row['Description'] if 'Description' in row and pd.notnull(
                row['Description']) else ''
            customer_part_number = row['Customer Part No'] if 'Customer Part No' in row and pd.notnull(
                row['Customer Part No']) else ''
            quantity = row['Qty/ Product'] if 'Qty/ Product' in row and pd.notnull(
                row['Qty/ Product']) else 0
            uom = row['UOM'] if 'UOM' in row and pd.notnull(row['UOM']) else ''
            ecn = row['ECN'] if 'ECN' in row and pd.notnull(row['ECN']) else ''
            msl = row['MSL'] if 'MSL' in row and pd.notnull(row['MSL']) else ''
            remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
                row['Remarks']) else ''

            bom_line_item, created = BillOfMaterialsLineItem.objects.update_or_create(
                part_number=row['VEPL Part No'],
                bom=bom,
                defaults={
                    'level': level,
                    'priority_level': priority_level,
                    'value': value,
                    'pcb_footprint': pcb_footprint,
                    'line_item_type': line_item_type,
                    'description': description,
                    'customer_part_number': customer_part_number,
                    'quantity': quantity,
                    'remarks': remarks,
                    'uom': uom,
                    'ecn': ecn,
                    'msl': msl,
                    'assembly_stage': assembly_stage
                }
            )

            if pd.notnull(row['Mfr']):
                parts = [part.strip()
                         for part in row['Mfr'].split('\n') if part.strip()]
                manufacturers = parts if not row['Mfr'].startswith(
                    '\n') else parts[1:]
            else:
                manufacturers = []

            if pd.notnull(row['Mfr. Part No']):
                parts = [part.strip()
                         for part in row['Mfr. Part No'].split('\n') if part.strip()]
                manufacturer_part_nos = parts if not row['Mfr. Part No'].startswith(
                    '\n') else parts[1:]
            else:
                manufacturer_part_nos = []

            print('manufacturer parts', manufacturer_part_nos)

            bom_line_item.manufacturer_parts.clear()
            for mfr, mfr_part_no in zip(manufacturers, manufacturer_part_nos):
                if mfr.strip() and mfr_part_no.strip():
                    manufacturer, _ = Manufacturer.objects.get_or_create(
                        name=mfr.strip())
                    manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                        part_number=mfr_part_no.strip(),
                        manufacturer=manufacturer
                    )

                    bom_line_item.manufacturer_parts.add(manufacturer_part)
            bom_line_item.save()

            if 'Reference' in row and pd.notnull(row['Reference']):
                for reference in row['Reference'].split(','):
                    ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
                        name=reference.strip(),
                        bom_line_item=bom_line_item
                    )

            bom_items_serializer = BillOfMaterialsLineItemSerializer(
                bom.bom_line_items, many=True)

    return Response({
        'message': 'BOM uploaded successfully',
        'bom_items': bom_items_serializer.data,
    }, status=status.HTTP_201_CREATED)

    # except Exception as e:
    #     # Handle exceptions
    #     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def scan_code(request):
    print(request.data)
    # input_string = "u1UUID000128808-VEPL145154751D<Facts>Q500"
    pattern = r'u1([^\-]+)-(VEPL\d{8})'
    match = re.search(pattern, request.data.get('value'))

    if match:
        uuid = match.group(1)
        part_number = match.group(2)

        print("UUID:", uuid)
        print("Part Number:", part_number)

        active_bom = ChecklistSetting.objects.first().active_bom
        active_checklist = ChecklistSetting.objects.first().active_checklist

        is_present = False
        is_quantity_sufficient = False

        if active_bom and active_checklist:
            for bom_line_item in active_bom.bom_line_items.all():
                if bom_line_item.part_number.strip() == part_number.strip():
                    is_present = True
                    checklist_item, created = ChecklistItem.objects.get_or_create(
                        checklist=active_checklist,
                        bom_line_item=bom_line_item,
                        required_quantity=bom_line_item.quantity,
                    )

                    if created:
                        checklist_item.present_quantity = 1
                    else:
                        checklist_item.present_quantity += 1

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
        if ChecklistSetting.objects.exists():
            setting = ChecklistSetting.objects.first()
            print('exists')
        else:
            setting = ChecklistSetting.objects.create(
                active_bom=BillOfMaterials.objects.get(id=bom_id))
            print('doesnt exist')
        setting.active_bom = active_bom
        setting.active_checklist = Checklist.objects.create(
            bom=active_bom, status='In Progress')
        setting.save()

        for bom_line_item in active_bom.bom_line_items.all():
            check_list_item, created = ChecklistItem.objects.get_or_create(
                checklist=setting.active_checklist,
                bom_line_item=bom_line_item,
                required_quantity=bom_line_item.quantity,
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
                active_bom=BillOfMaterials.objects.get(id=bom_id))

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
                setting = ChecklistSetting.objects.first()
                setting.active_checklist = None
                setting.active_bom = None
                setting.save()
            checklist_serializer = ChecklistSerializer(checklist)

            return Response(
                {
                    'checklist': checklist_serializer.data,
                }, status=status.HTTP_200_OK
            )
        else:
            return Response({'error': 'The selcted BOM is not active, please make the BOM active by genrating a checklist'}, status=status.HTTP_400_BAD_REQUEST)

    except ChecklistSetting.DoesNotExist:
        setting = ChecklistSetting.objects.create(
            active_bom=BillOfMaterials.objects.get(id=bom_id))
        setting.active_checklist = Checklist.objects.create(
            bom=BillOfMaterials.objects.get(id=bom_id), status='In Progress')
        setting.save()
        return Response({'message': 'Active Checklist and BOM not defined but new ones set successfully'}, status=status.HTTP_200_OK)

    except BillOfMaterials.DoesNotExist:
        return Response({'error': 'BOM not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_checklist_details(request,checklist_id):
    try:
        checklist  = Checklist.objects.get(pk = checklist_id)
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
        # Retrieve all BOM objects from the database
        boms = BillOfMaterials.objects.all()

        # Serialize the BOM objects
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
                active_bom=BillOfMaterials.objects.get(id=checklist.bom.id))

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
def save_qr_code(request,checklist_id):
    try:
        print(request.data)
        checklist  = Checklist.objects.get(pk = checklist_id)
        checklist.qr_code_link = request.data.get('qrCodeDataURL', None)
        checklist.unique_code = request.data.get('uniqueCode', None)
        checklist.save()
        checklist_serializer = ChecklistSerializer(checklist)
        return Response({'checklist': checklist_serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)