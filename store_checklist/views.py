from django.shortcuts import render
from .models import *
from rest_framework.decorators import api_view,authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .serializers import *
import pandas as pd
import json
from django.db.models import Q

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


@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def test_api(request):
    # if 'file' not in request.FILES:
    #     return Response({'error': 'File is missing'}, status=status.HTTP_400_BAD_REQUEST)

    # try:
        # Read the Excel file using pandas
        # file = request.FILES['file']
        file_path = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
        data = pd.read_excel(file_path, header=5,sheet_name=1).head(10)

        # data = pd.read_excel(file)
        bom  = BillOfMaterials.objects.all()[0]
        # Process each row
        for _, row in data.iterrows():
            if _ == 1:
                print(row)
                assembly_stage, _ = AssemblyStage.objects.get_or_create(name=row.get('Assy Stage', None))
                line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(name=row.get('Type', None))
                
                level = row['Level'] if pd.notnull(row['Level']) else 0
                priority_level = row['Prioprity Level'] if pd.notnull(row['Prioprity Level']) else 0
                value = row['Value'] if pd.notnull(row['Value']) else ''
                pcb_footprint = row['PCB Footprint'] if pd.notnull(row['PCB Footprint']) else ''
                description = row['Description'] if pd.notnull(row['Description']) else ''
                customer_part_number = row['Customer Part No'] if pd.notnull(row['Customer Part No']) else ''
                quantity = row['Qty/ Product'] if pd.notnull(row['Qty/ Product']) else 0
                uom = row['UOM'] if pd.notnull(row['UOM']) else ''
                ecn = row['ECN'] if pd.notnull(row['ECN']) else ''
                msl = row['MSL'] if pd.notnull(row['MSL']) else ''
                remarks = row['Remarks'] if pd.notnull(row['Remarks']) else ''

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
                if row['Mfr'].startswith('\n'):
                    row['Mfr'] = row['Mfr'].lstrip('\n')
                if row['Mfr. Part No'].startswith('\n'):
                    row['Mfr. Part No'] = row['Mfr. Part No'].lstrip('\n')
                print(row['Mfr'])
                print(row['Mfr. Part No'])
                manufacturers = row['Mfr'].split('\n') if pd.notnull(row['Mfr']) else []
                manufacturer_part_nos = row['Mfr. Part No'].split('\n') if pd.notnull(row['Mfr. Part No']) else []
                for mfr, mfr_part_no in zip(manufacturers, manufacturer_part_nos):
                    if mfr.strip() and mfr_part_no.strip():
                        manufacturer, _ = Manufacturer.objects.get_or_create(name=mfr.strip())
                        manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                            part_number=mfr_part_no.strip(),
                            manufacturer=manufacturer
                        )

                        bom_line_item.manufacturer_parts.add(manufacturer_part)
                bom_line_item.save()

        return Response({'message': 'BOM uploaded successfully'}, status=status.HTTP_201_CREATED)

    # except Exception as e:
    #     # Handle exceptions
    #     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
