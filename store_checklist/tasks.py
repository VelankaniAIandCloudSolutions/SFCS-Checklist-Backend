from accounts.serializers import *
from .models import Order
from celery import current_task, shared_task
import pandas as pd
from django.db import transaction
from .models import *
from accounts.models import UserAccount
from .serializers import BillOfMaterialsLineItemSerializer
from django.utils import timezone
import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
logger = logging.getLogger(__name__)


@shared_task
def test_func(x, y):
    return x + y


@shared_task
def send_notification_email(subject, message, recipient_list):
    send_mail(subject, message, 'your@example.com', recipient_list)


@shared_task
def process_bom_file(bom_file, bom_file_name, data, user_id):
    try:
        user = UserAccount.objects.get(pk=user_id)

        # file_path  = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
        bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

        # product, _ = Product.objects.get_or_create(
        #     name=data.get('product_name'),
        #     product_code=data.get('product_code'),
        #     defaults={
        #         'product_rev_number': data.get('product_rev_no'),
        #         'updated_by': user,
        #         'created_by': user,
        #     }
        # )

        product = Product.objects.get(id=data.get('product_id'))

        bom_type, _ = BillOfMaterialsType.objects.get_or_create(
            name=data.get('bom_type'),
            defaults={
                'updated_by': user,
                'created_by': user,
            })
        if (str(data.get('issue_date')) == ''):
            issue_date = timezone.now().date()
        else:
            issue_date = data.get('issue_date')

        bom, _ = BillOfMaterials.objects.get_or_create(
            product=product,
            issue_date=issue_date,
            bom_file_name=bom_file_name,


            defaults={
                'bom_type': bom_type,
                'bom_rev_number': data.get('bom_rev_no'),
                'change_note': data.get('bom_rev_change_note'),
                'bom_file': 'bom_files/' + bom_file_name,
                'updated_by': user,
                'created_by': user,
            }
        )

        with transaction.atomic():
            bom_line_items_to_create = []
            vepl_to_manufacturer_mapping = {}
            vepl_to_references_mapping = {}
            for _, row in bom_file_data.iterrows():
                # print(row)
                if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
                    vepl_part_no = row['VEPL Part No']

                    if pd.notnull(row['Mfr']):
                        parts = [str(part).strip()
                                 for part in str(row['Mfr']).split('\n') if str(part).strip()]
                        manufacturers = parts if not str(row['Mfr']).startswith(
                            '\n') else parts[1:]
                    else:
                        manufacturers = []

                    if pd.notnull(row['Mfr. Part No']):
                        parts = [str(part).strip()
                                 for part in str(row['Mfr. Part No']).split('\n') if str(part).strip()]
                        manufacturer_part_nos = parts if not str(row['Mfr. Part No']).startswith(
                            '\n') else parts[1:]
                    else:
                        manufacturer_part_nos = []

                    for mfr, mfr_part_no in zip(manufacturers, manufacturer_part_nos):
                        if str(mfr).strip() and str(mfr_part_no).strip():
                            manufacturer, _ = Manufacturer.objects.get_or_create(
                                name=str(mfr).strip(),
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                            manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                                part_number=str(mfr_part_no).strip(),
                                manufacturer=manufacturer,
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )

                            if vepl_part_no not in vepl_to_manufacturer_mapping:
                                vepl_to_manufacturer_mapping[vepl_part_no] = []

                            vepl_to_manufacturer_mapping[vepl_part_no].append(
                                manufacturer_part)

                    if 'Reference' in row and pd.notnull(row['Reference']):
                        for reference in str(row['Reference']).split(','):
                            ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
                                name=str(reference).strip(),
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                            if vepl_part_no not in vepl_to_references_mapping:
                                vepl_to_references_mapping[vepl_part_no] = []

                            vepl_to_references_mapping[vepl_part_no].append(
                                ref.name)

                    assembly_stage, _ = AssemblyStage.objects.get_or_create(
                        name=row.get('Assy Stage', None),
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        })
                    line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
                        name=str(row.get('Type')).strip().upper(),
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        })
                    checklist_item_type_value = ''
                    if (row.get('Type')):
                        if str(row.get('Type')).strip().upper() == 'PCB':
                            checklist_item_type_value = 'PCB'
                        elif str(row.get('Type')).strip().upper() == 'PCB SERIAL NUMBER LABEL':
                            checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER PASTE':
                            checklist_item_type_value = 'SOLDER PASTE'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER BAR':
                            checklist_item_type_value = 'SOLDER BAR'
                        elif str(row.get('Type')).strip().upper() == 'IPA':
                            checklist_item_type_value = 'IPA'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER FLUX':
                            checklist_item_type_value = 'SOLDER FLUX'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER WIRE':
                            checklist_item_type_value = 'SOLDER WIRE'
                        elif str(row.get('Type')).strip().upper() == 'SMT PALLET':
                            checklist_item_type_value = 'SMT PALLET'
                        elif str(row.get('Type')).strip().upper() == 'WAVE PALLET':
                            checklist_item_type_value = 'WAVE PALLET'
                        else:
                            checklist_item_type_value = 'RAW MATERIAL'

                    checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
                        'updated_by': user,
                        'created_by': user,
                    })

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
                    uom = row['UOM'] if 'UOM' in row and pd.notnull(
                        row['UOM']) else ''
                    ecn = row['ECN'] if 'ECN' in row and pd.notnull(
                        row['ECN']) else ''
                    msl = row['MSL'] if 'MSL' in row and pd.notnull(
                        row['MSL']) else ''
                    remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
                        row['Remarks']) else ''

                    existing_item = BillOfMaterialsLineItem.objects.filter(
                        part_number=row['VEPL Part No'], bom=bom).first()

                    if existing_item:
                        existing_item.level = level
                        existing_item.priority_level = priority_level
                        existing_item.value = value
                        existing_item.pcb_footprint = pcb_footprint
                        existing_item.line_item_type = line_item_type
                        existing_item.description = description
                        existing_item.customer_part_number = customer_part_number
                        existing_item.quantity = quantity
                        existing_item.remarks = remarks
                        existing_item.uom = uom
                        existing_item.ecn = ecn
                        existing_item.msl = msl
                        existing_item.assembly_stage = assembly_stage
                        existing_item.updated_by = user
                        existing_item.created_by = user
                        if existing_item.part_number in vepl_to_manufacturer_mapping:
                            existing_item.manufacturer_parts.set(
                                vepl_to_manufacturer_mapping[vepl_part_no])

                        if existing_item.part_number in vepl_to_references_mapping:
                            reference = BillOfMaterialsLineItemReference.objects.filter(
                                name=vepl_to_references_mapping[vepl_part_no]).first()
                            reference.bom_line_item = existing_item
                            reference.save()

                        existing_item.save()

                    else:
                        bom_line_items_to_create.append(BillOfMaterialsLineItem(
                            part_number=row['VEPL Part No'],
                            bom=bom,
                            level=level,
                            priority_level=priority_level,
                            value=value,
                            pcb_footprint=pcb_footprint,
                            line_item_type=line_item_type,
                            description=description,
                            customer_part_number=customer_part_number,
                            quantity=quantity,
                            remarks=remarks,
                            uom=uom,
                            ecn=ecn,
                            msl=msl,
                            assembly_stage=assembly_stage,
                            created_by=user,
                            updated_by=user
                        ))

            BillOfMaterialsLineItem.objects.bulk_create(
                bom_line_items_to_create)

            bom_line_items = BillOfMaterialsLineItem.objects.filter(bom=bom)
            for bom_line_item in bom_line_items:
                vepl_part_no = bom_line_item.part_number

                if vepl_part_no in vepl_to_manufacturer_mapping:
                    bom_line_item.manufacturer_parts.set(
                        vepl_to_manufacturer_mapping[vepl_part_no])
                    bom_line_item.save()

                if vepl_part_no in vepl_to_references_mapping:
                    for ref in vepl_to_references_mapping[vepl_part_no]:
                        reference = BillOfMaterialsLineItemReference.objects.filter(
                            name=ref).first()
                    if reference:
                        if reference.bom_line_item:
                            reference.bom_line_item = bom_line_item
                            reference.save()
                        # else:
                        #     current_task.logger.warning(
                        #         f"Warning: Bom line item not found for reference {ref_name}")
                    # else:
                    #     current_task.logger.warning(
                    #         f"Warning: Reference {ref} not found in the database.")

            print(bom_line_items.first().id)

            # bom_items_serializer = BillOfMaterialsLineItemSerializer(bom.bom_line_items, many=True)

        return 'BOM Uploaded Successfully'

    except Exception as e:
        logger.info(f"Exception in process_bom_file task: {str(e)}")
        return ('BOM Upload Failed', 'FAILURE', str(e))


# @shared_task
# def process_bom_file_new(bom_file, bom_file_name, data, user_id):
#     try:
#         # Assuming 'user' is defined somewhere in your code

#         # Get the uploaded file from the request
#         user = UserAccount.objects.get(pk=user_id)
#         bom_format_id = data.get('bom_format_id')
#         bom_format = BomFormat.objects.get(pk=bom_format_id)

#         bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

#         product = Product.objects.get(id=data.get('product_id'))

#         bom_type, _ = BillOfMaterialsType.objects.get_or_create(
#             name=data.get('bom_type'),
#             defaults={
#                 'updated_by': user,
#                 'created_by': user,
#             })

#         if (str(data.get('issue_date')) == ''):
#             issue_date = timezone.now().date()
#         else:
#             issue_date = data.get('issue_date')

#         pcb_file_name = data.get('pcb_file_name')
#         pcb_bbt_test_report_file = None
#         if pcb_file_name:
#             pcb_bbt_test_report_file = 'pcb_bbt_test_report_files/' + pcb_file_name

#         bom, _ = BillOfMaterials.objects.get_or_create(
#             product=product,
#             bom_file_name=bom_file_name,
#             bom_rev_number=data.get('bom_rev_no'),
#             bom_format=bom_format,

#             defaults={
#                 'bom_type': bom_type,
#                 'change_note': data.get('bom_rev_change_note'),
#                 'issue_date': issue_date,
#                 'pcb_file_name': pcb_file_name,
#                 'pcb_bbt_test_report_file': pcb_bbt_test_report_file,
#                 'bom_file': 'bom_files/' + bom_file_name,
#                 'updated_by': user,
#                 'created_by': user,
#             })

#         print('bom created')

#         if "Hardware Design" in bom.bom_format.name:

#             # Drop rows where 'vepl part' is NaN
#             print("NaN count before dropna:",
#                   bom_file_data['VEPL Part No'].isnull().sum())
#             bom_file_data = bom_file_data.dropna(subset=['VEPL Part No'])
#             print("NaN count after dropna:",
#                   bom_file_data['VEPL Part No'].isnull().sum())

#             # bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
#             #     'VEPL')]

#             if not bom_file_data.empty:

#                 print("Before filtering - Row count:", len(bom_file_data))

#                 print(bom_file_data['VEPL Part No'])

#                 # bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
#                 #     'VEPL')]
#                 bom_file_data['VEPL Part No'] = bom_file_data['VEPL Part No'].astype(
#                     str)

#                 bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.strip(
#                 ).str.startswith('VEPL')]

#                 print(bom_file_data['VEPL Part No'])

#                 print("After filtering - Row count:", len(bom_file_data))
#                 print("Filtered DataFrame:")
#                 print(bom_file_data)
#             else:
#                 print("No rows left in DataFrame after dropping NaN values.")

#             # Reset index after dropping rows
#             bom_file_data.reset_index(drop=True, inplace=True)

#             # Forward fill
#             bom_file_data.ffill(inplace=True)

#             # Lists to store instances and mapping

#             with transaction.atomic():
#                 bom_line_items_to_create = []
#                 print('isnide tansaction.atomic', bom_line_items_to_create)
#                 vepl_to_references_mapping = {}
#                 vepl_to_manufacturer_mapping = {}
#                 processed_part_numbers = set()

#                 # Iterate through rows in the DataFrame
#                 for _, row in bom_file_data.head().iterrows():
#                     print('index', _)

#                     if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
#                         vepl_part_no = row['VEPL Part No']
#                         # print('Processing VEPL Part No:', vepl_part_no)
#                         # Handling 'Mfr' field
#                         if ('Mfr' in row and pd.notnull(row['Mfr'])) or ('Manufacturer' in row and pd.notnull(row['Manufacturer'])):
#                             mfr_name = str(
#                                 row.get('Mfr')).strip().replace('\n', '')
#                             manufacturer, _ = Manufacturer.objects.get_or_create(
#                                 name=mfr_name,
#                                 defaults={
#                                     'updated_by': user,
#                                     'created_by': user,
#                                     # Add other fields if needed
#                                 })
#                             # print('mfr created in db')
#                         else:
#                             manufacturer = None

#                         # if pd.notnull(row['Mfr. Part No']):
#                         #     mfr_part_no = str(row.get('Mfr. Part No')
#                         #                       ).strip().replace('\n', '')
#                         #     manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
#                         #         part_number=mfr_part_no,
#                         #         manufacturer=manufacturer,
#                         #         defaults={
#                         #             'updated_by': user,
#                         #             'created_by': user,

#                         #         })
#                         if pd.notnull(row.get('Mfr. Part No', None)) or pd.notnull(row.get('Mfr.Part No', None)):
#                             mfr_part_no = str(row.get('Mfr. Part No', row.get(
#                                 'Mfr.Part No', ''))).strip().replace('\n', '')
#                             # Check if either 'Mfr. Part No' or 'Mfr.Part No' column is not null
#                             manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
#                                 part_number=mfr_part_no,
#                                 manufacturer=manufacturer,
#                                 defaults={
#                                     'updated_by': user,
#                                     'created_by': user,
#                                 }
#                             )

#                             # print('mfr  aprt created in db')
#                         else:
#                             manufacturer_part = None

#                         if vepl_part_no not in vepl_to_manufacturer_mapping:
#                             vepl_to_manufacturer_mapping[vepl_part_no] = []

#                         vepl_to_manufacturer_mapping[vepl_part_no].append(
#                             manufacturer_part)

#                         # Handling 'Reference' field
#                         if 'Reference' in row and pd.notnull(row['Reference']):
#                             # print('Entering Reference block for row:', row)
#                             for reference in str(row['Reference']).split(','):

#                                 # print('ref entry done in db')

#                                 if vepl_part_no not in vepl_to_references_mapping:
#                                     vepl_to_references_mapping[vepl_part_no] = [
#                                     ]

#                                 vepl_to_references_mapping[vepl_part_no].append(
#                                     str(reference.strip()))
#                                 # print('vepl_to_references_mapping in loop',vepl_to_references_mapping)

#                         assembly_stage, _ = AssemblyStage.objects.get_or_create(
#                             name=row.get('Assy Stage', None),
#                             defaults={
#                                 'updated_by': user,
#                                 'created_by': user,
#                             })
#                         line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
#                             name=str(row.get('Type')).strip().upper(),
#                             defaults={
#                                 'updated_by': user,
#                                 'created_by': user,
#                             })

#                         checklist_item_type_value = ''
#                         if (row.get('Type')):
#                             if str(row.get('Type')).strip().upper() == 'PCB':
#                                 checklist_item_type_value = 'PCB'
#                             elif str(row.get('Type')).strip().upper() == 'PCB SERIAL NUMBER LABEL':
#                                 checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
#                             elif str(row.get('Type')).strip().upper() == 'SOLDER PASTE':
#                                 checklist_item_type_value = 'SOLDER PASTE'
#                             elif str(row.get('Type')).strip().upper() == 'SOLDER BAR':
#                                 checklist_item_type_value = 'SOLDER BAR'
#                             elif str(row.get('Type')).strip().upper() == 'IPA':
#                                 checklist_item_type_value = 'IPA'
#                             elif str(row.get('Type')).strip().upper() == 'SOLDER FLUX':
#                                 checklist_item_type_value = 'SOLDER FLUX'
#                             elif str(row.get('Type')).strip().upper() == 'SOLDER WIRE':
#                                 checklist_item_type_value = 'SOLDER WIRE'
#                             elif str(row.get('Type')).strip().upper() == 'SMT PALLET':
#                                 checklist_item_type_value = 'SMT PALLET'
#                             elif str(row.get('Type')).strip().upper() == 'WAVE PALLET':
#                                 checklist_item_type_value = 'WAVE PALLET'
#                             else:
#                                 checklist_item_type_value = 'RAW MATERIAL'

#                         checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
#                             'updated_by': user,
#                             'created_by': user,
#                         })

#                         level = row['Level'] if 'Level' in row and pd.notnull(
#                             row['Level']) else ''
#                         priority_level = row.get('Prioprity Level') if 'Prioprity Level' in row and pd.notnull(
#                             row['Prioprity Level']) else \
#                             row.get('Priority Level') if 'Priority Level' in row and pd.notnull(
#                                 row['Priority Level']) else ''
#                         value = row['Value'] if 'Value' in row and pd.notnull(
#                             row['Value']) else ''
#                         pcb_footprint = row['PCB Footprint'] if 'PCB Footprint' in row and pd.notnull(
#                             row['PCB Footprint']) else ''
#                         description = row['Description'] if 'Description' in row and pd.notnull(
#                             row['Description']) else \
#                             row.get('Description/part') if 'Description/part' in row and pd.notnull(
#                                 row['Description/part']) else ''
#                         customer_part_number = row['Customer Part No'] if 'Customer Part No' in row and pd.notnull(
#                             row['Customer Part No']) else ''

#                         quantity_column_names = [
#                             'Qty/ Product', 'Qty/Product', 'Quantity']

#                         # Loop through possible column names to find the quantity
#                         for qty_col_name in quantity_column_names:
#                             if qty_col_name in row and pd.notnull(row[qty_col_name]):
#                                 quantity = row[qty_col_name]
#                                 break
#                         else:
#                             quantity = 0

#                         # quantity = row['Qty/ Product'] if 'Qty/ Product' in row and pd.notnull(
#                         #     row['Qty/ Product']) else 0
#                         uom = row['UOM'] if 'UOM' in row and pd.notnull(
#                             row['UOM']) else ''
#                         ecn = row['ECN'] if 'ECN' in row and pd.notnull(
#                             row['ECN']) else ''
#                         msl = row['MSL'] if 'MSL' in row and pd.notnull(
#                             row['MSL']) else ''
#                         remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
#                             row['Remarks']) else ''

#                         existing_item = BillOfMaterialsLineItem.objects.filter(
#                             part_number=row['VEPL Part No'], bom=bom).first()

#                         if existing_item:
#                             existing_item.level = level
#                             existing_item.priority_level = priority_level
#                             existing_item.value = value
#                             existing_item.pcb_footprint = pcb_footprint
#                             existing_item.line_item_type = line_item_type
#                             existing_item.description = description
#                             existing_item.customer_part_number = customer_part_number
#                             existing_item.quantity = quantity
#                             existing_item.remarks = remarks
#                             existing_item.uom = uom
#                             existing_item.ecn = ecn
#                             existing_item.msl = msl
#                             existing_item.assembly_stage = assembly_stage
#                             existing_item.updated_by = user
#                             existing_item.created_by = user

#                             if existing_item.part_number in vepl_to_references_mapping:
#                                 existing_references = BillOfMaterialsLineItemReference.objects.filter(
#                                     name=vepl_to_references_mapping[vepl_part_no], bom_line_item=existing_item)
#                                 if existing_references:
#                                     pass
#                                 else:
#                                     BillOfMaterialsLineItemReference.objects.create(
#                                         name=vepl_to_references_mapping[vepl_part_no], bom_line_item=existing_item, updated_by=user, created_by=user)

#                             if existing_item.part_number in vepl_to_manufacturer_mapping:
#                                 existing_item.manufacturer_parts.set(
#                                     vepl_to_manufacturer_mapping[vepl_part_no])
#                             existing_item.save()

#                         else:

#                             # Other fields handling...
#                             # Create BillOfMaterialsLineItem instance
#                             # print('if not an existing item')
#                             bom_line_item = BillOfMaterialsLineItem(
#                                 part_number=row['VEPL Part No'],
#                                 bom=bom,
#                                 level=level,
#                                 priority_level=priority_level,
#                                 value=value,
#                                 pcb_footprint=pcb_footprint,
#                                 line_item_type=line_item_type,
#                                 description=description,
#                                 customer_part_number=customer_part_number,
#                                 quantity=quantity,
#                                 remarks=remarks,
#                                 uom=uom,
#                                 ecn=ecn,
#                                 msl=msl,
#                                 assembly_stage=assembly_stage,
#                                 created_by=user,
#                                 updated_by=user
#                             )
#                             bom_line_items_to_create.append(bom_line_item)
#                             dupli_count = 0
#                             for bom_line_item in bom_line_items_to_create:
#                                 if bom_line_item.part_number == row['VEPL Part No']:
#                                     dupli_count += 1
#                                     # print(str(bom_line_item.part_number) + 'exists')
#                             if dupli_count > 1:
#                                 # print('dupli count exceeded')
#                                 bom_line_items_to_create.remove(bom_line_item)

#                 BillOfMaterialsLineItem.objects.bulk_create(
#                     bom_line_items_to_create)

#                 # print('line items created')

#                 bom_line_items = BillOfMaterialsLineItem.objects.filter(
#                     bom=bom)
#                 for bom_line_item in bom_line_items:
#                     vepl_part_no = bom_line_item.part_number
#                     if vepl_part_no in vepl_to_manufacturer_mapping:
#                         bom_line_item.manufacturer_parts.set(
#                             vepl_to_manufacturer_mapping[vepl_part_no])
#                         bom_line_item.save()
#                     # print('final', vepl_to_references_mapping)
#                     if vepl_part_no in vepl_to_references_mapping:
#                         for ref in set(vepl_to_references_mapping[vepl_part_no]):
#                             # print('current ref in loop ', ref)
#                             BillOfMaterialsLineItemReference.objects.create(
#                                 name=ref, bom_line_item=bom_line_item, updated_by=user, created_by=user)
#                             # reference = BillOfMaterialsLineItemReference.objects.filter(
#                             #     name=ref).first()

#                             # if reference:
#                             #     print('got ref ', reference)
#                             #     if reference.bom_line_item:
#                             #         reference.bom_line_item = bom_line_item
#                             #         reference.save()
#                             #         print('saved ref ', reference)
#                             #     else:
#                             #         print(
#                             #             'bom_line_item is None for reference ', reference)

#                 print('outside the loop , check if it reaches here')

#             return 'BOM Uploaded Successfully'

#         else:
#             pass

#         # Read the Excel file directly from the file object

#     except Exception as e:
#         return ('BOM Upload Failed', 'FAILURE', str(e))

@shared_task
def process_bom_file_new(bom_file, bom_file_name, data, user_id):
    try:
        # Assuming 'user' is defined somewhere in your code

        # Get the uploaded file from the request
        user = UserAccount.objects.get(pk=user_id)
        bom_format_id = data.get('bom_format_id')
        bom_format = BomFormat.objects.get(
            pk=bom_format_id) if bom_format_id else None

        bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

        product = Product.objects.get(id=data.get('product_id'))

        bom_type, _ = BillOfMaterialsType.objects.get_or_create(
            name=data.get('bom_type'),
            defaults={
                'updated_by': user,
                'created_by': user,
            })

        if (str(data.get('issue_date')) == ''):
            issue_date = timezone.now().date()
        else:
            issue_date = data.get('issue_date')

        pcb_file_name = data.get('pcb_file_name')
        pcb_bbt_test_report_file = None
        if pcb_file_name:
            pcb_bbt_test_report_file = 'pcb_bbt_test_report_files/' + pcb_file_name

        bom, _ = BillOfMaterials.objects.get_or_create(
            product=product,
            bom_file_name=bom_file_name,
            bom_rev_number=data.get('bom_rev_no'),
            bom_format=bom_format,

            defaults={
                'bom_type': bom_type,
                'change_note': data.get('bom_rev_change_note'),
                'issue_date': issue_date,
                'pcb_file_name': pcb_file_name,
                'pcb_bbt_test_report_file': pcb_bbt_test_report_file,
                'bom_file': 'bom_files/' + bom_file_name,
                'updated_by': user,
                'created_by': user,
            })

        print('bom created')

        if bom_format is None or "Hardware Design" in bom.bom_format.name:
            # Drop rows where 'vepl part' is NaN
            print("NaN count before dropna:",
                  bom_file_data['VEPL Part No'].isnull().sum())
            bom_file_data = bom_file_data.dropna(subset=['VEPL Part No'])
            print("NaN count after dropna:",
                  bom_file_data['VEPL Part No'].isnull().sum())

            # bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
            #     'VEPL')]

            if not bom_file_data.empty:

                print("Before filtering - Row count:", len(bom_file_data))

                print(bom_file_data['VEPL Part No'])

                # bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
                #     'VEPL')]
                bom_file_data['VEPL Part No'] = bom_file_data['VEPL Part No'].astype(
                    str)

                bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.strip(
                ).str.startswith('VEPL')]

                print(bom_file_data['VEPL Part No'])

                print("After filtering - Row count:", len(bom_file_data))
                print("Filtered DataFrame:")
                print(bom_file_data)
            else:
                print("No rows left in DataFrame after dropping NaN values.")

            # Reset index after dropping rows
            bom_file_data.reset_index(drop=True, inplace=True)

            # Forward fill
            bom_file_data.ffill(inplace=True)

            # Lists to store instances and mapping

            with transaction.atomic():
                bom_line_items_to_create = []
                print('isnide tansaction.atomic', bom_line_items_to_create)
                vepl_to_references_mapping = {}
                vepl_to_manufacturer_mapping = {}
                processed_part_numbers = set()

                # Iterate through rows in the DataFrame
                for _, row in bom_file_data.head().iterrows():
                    print('index', _)

                    if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
                        vepl_part_no = row['VEPL Part No']
                        # print('Processing VEPL Part No:', vepl_part_no)
                        # Handling 'Mfr' field
                        if ('Mfr' in row and pd.notnull(row['Mfr'])) or ('Manufacturer' in row and pd.notnull(row['Manufacturer'])):
                            mfr_name = str(
                                row.get('Mfr')).strip().replace('\n', '')
                            manufacturer, _ = Manufacturer.objects.get_or_create(
                                name=mfr_name,
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                    # Add other fields if needed
                                })
                            # print('mfr created in db')
                        else:
                            manufacturer = None

                        # if pd.notnull(row['Mfr. Part No']):
                        #     mfr_part_no = str(row.get('Mfr. Part No')
                        #                       ).strip().replace('\n', '')
                        #     manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                        #         part_number=mfr_part_no,
                        #         manufacturer=manufacturer,
                        #         defaults={
                        #             'updated_by': user,
                        #             'created_by': user,

                        #         })
                        if pd.notnull(row.get('Mfr. Part No', None)) or pd.notnull(row.get('Mfr.Part No', None)):
                            mfr_part_no = str(row.get('Mfr. Part No', row.get(
                                'Mfr.Part No', ''))).strip().replace('\n', '')
                            # Check if either 'Mfr. Part No' or 'Mfr.Part No' column is not null
                            manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                                part_number=mfr_part_no,
                                manufacturer=manufacturer,
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )

                            # print('mfr  aprt created in db')
                        else:
                            manufacturer_part = None

                        if vepl_part_no not in vepl_to_manufacturer_mapping:
                            vepl_to_manufacturer_mapping[vepl_part_no] = []

                        vepl_to_manufacturer_mapping[vepl_part_no].append(
                            manufacturer_part)

                        # Handling 'Reference' field
                        if 'Reference' in row and pd.notnull(row['Reference']):
                            # print('Entering Reference block for row:', row)
                            for reference in str(row['Reference']).split(','):

                                # print('ref entry done in db')

                                if vepl_part_no not in vepl_to_references_mapping:
                                    vepl_to_references_mapping[vepl_part_no] = [
                                    ]

                                vepl_to_references_mapping[vepl_part_no].append(
                                    str(reference.strip()))
                                # print('vepl_to_references_mapping in loop',vepl_to_references_mapping)

                        assembly_stage, _ = AssemblyStage.objects.get_or_create(
                            name=row.get('Assy Stage', None),
                            defaults={
                                'updated_by': user,
                                'created_by': user,
                            })
                        line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
                            name=str(row.get('Type')).strip().upper(),
                            defaults={
                                'updated_by': user,
                                'created_by': user,
                            })

                        checklist_item_type_value = ''
                        if (row.get('Type')):
                            if str(row.get('Type')).strip().upper() == 'PCB':
                                checklist_item_type_value = 'PCB'
                            elif str(row.get('Type')).strip().upper() == 'PCB SERIAL NUMBER LABEL':
                                checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER PASTE':
                                checklist_item_type_value = 'SOLDER PASTE'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER BAR':
                                checklist_item_type_value = 'SOLDER BAR'
                            elif str(row.get('Type')).strip().upper() == 'IPA':
                                checklist_item_type_value = 'IPA'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER FLUX':
                                checklist_item_type_value = 'SOLDER FLUX'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER WIRE':
                                checklist_item_type_value = 'SOLDER WIRE'
                            elif str(row.get('Type')).strip().upper() == 'SMT PALLET':
                                checklist_item_type_value = 'SMT PALLET'
                            elif str(row.get('Type')).strip().upper() == 'WAVE PALLET':
                                checklist_item_type_value = 'WAVE PALLET'
                            else:
                                checklist_item_type_value = 'RAW MATERIAL'

                        checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
                            'updated_by': user,
                            'created_by': user,
                        })

                        level = row['Level'] if 'Level' in row and pd.notnull(
                            row['Level']) else ''
                        priority_level = row.get('Prioprity Level') if 'Prioprity Level' in row and pd.notnull(
                            row['Prioprity Level']) else \
                            row.get('Priority Level') if 'Priority Level' in row and pd.notnull(
                                row['Priority Level']) else ''
                        value = row['Value'] if 'Value' in row and pd.notnull(
                            row['Value']) else ''
                        pcb_footprint = row['PCB Footprint'] if 'PCB Footprint' in row and pd.notnull(
                            row['PCB Footprint']) else ''
                        description = row['Description'] if 'Description' in row and pd.notnull(
                            row['Description']) else \
                            row.get('Description/part') if 'Description/part' in row and pd.notnull(
                                row['Description/part']) else ''
                        customer_part_number = row['Customer Part No'] if 'Customer Part No' in row and pd.notnull(
                            row['Customer Part No']) else ''

                        quantity_column_names = [
                            'Qty/ Product', 'Qty/Product', 'Quantity']

                        # Loop through possible column names to find the quantity
                        for qty_col_name in quantity_column_names:
                            if qty_col_name in row and pd.notnull(row[qty_col_name]):
                                quantity = row[qty_col_name]
                                break
                        else:
                            quantity = 0

                        # quantity = row['Qty/ Product'] if 'Qty/ Product' in row and pd.notnull(
                        #     row['Qty/ Product']) else 0
                        uom = row['UOM'] if 'UOM' in row and pd.notnull(
                            row['UOM']) else ''
                        ecn = row['ECN'] if 'ECN' in row and pd.notnull(
                            row['ECN']) else ''
                        msl = row['MSL'] if 'MSL' in row and pd.notnull(
                            row['MSL']) else ''
                        remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
                            row['Remarks']) else ''

                        existing_item = BillOfMaterialsLineItem.objects.filter(
                            part_number=row['VEPL Part No'], bom=bom).first()

                        if existing_item:
                            existing_item.level = level
                            existing_item.priority_level = priority_level
                            existing_item.value = value
                            existing_item.pcb_footprint = pcb_footprint
                            existing_item.line_item_type = line_item_type
                            existing_item.description = description
                            existing_item.customer_part_number = customer_part_number
                            existing_item.quantity = quantity
                            existing_item.remarks = remarks
                            existing_item.uom = uom
                            existing_item.ecn = ecn
                            existing_item.msl = msl
                            existing_item.assembly_stage = assembly_stage
                            existing_item.updated_by = user
                            existing_item.created_by = user

                            if existing_item.part_number in vepl_to_references_mapping:
                                existing_references = BillOfMaterialsLineItemReference.objects.filter(
                                    name=vepl_to_references_mapping[vepl_part_no], bom_line_item=existing_item)
                                if existing_references:
                                    pass
                                else:
                                    BillOfMaterialsLineItemReference.objects.create(
                                        name=vepl_to_references_mapping[vepl_part_no], bom_line_item=existing_item, updated_by=user, created_by=user)

                            if existing_item.part_number in vepl_to_manufacturer_mapping:
                                existing_item.manufacturer_parts.set(
                                    vepl_to_manufacturer_mapping[vepl_part_no])
                            existing_item.save()

                        else:

                            # Other fields handling...
                            # Create BillOfMaterialsLineItem instance
                            # print('if not an existing item')
                            bom_line_item = BillOfMaterialsLineItem(
                                part_number=row['VEPL Part No'],
                                bom=bom,
                                level=level,
                                priority_level=priority_level,
                                value=value,
                                pcb_footprint=pcb_footprint,
                                line_item_type=line_item_type,
                                description=description,
                                customer_part_number=customer_part_number,
                                quantity=quantity,
                                remarks=remarks,
                                uom=uom,
                                ecn=ecn,
                                msl=msl,
                                assembly_stage=assembly_stage,
                                created_by=user,
                                updated_by=user
                            )
                            bom_line_items_to_create.append(bom_line_item)
                            dupli_count = 0
                            for bom_line_item in bom_line_items_to_create:
                                if bom_line_item.part_number == row['VEPL Part No']:
                                    dupli_count += 1
                                    # print(str(bom_line_item.part_number) + 'exists')
                            if dupli_count > 1:
                                # print('dupli count exceeded')
                                bom_line_items_to_create.remove(bom_line_item)

                BillOfMaterialsLineItem.objects.bulk_create(
                    bom_line_items_to_create)

                # print('line items created')

                bom_line_items = BillOfMaterialsLineItem.objects.filter(
                    bom=bom)
                for bom_line_item in bom_line_items:
                    vepl_part_no = bom_line_item.part_number
                    if vepl_part_no in vepl_to_manufacturer_mapping:
                        bom_line_item.manufacturer_parts.set(
                            vepl_to_manufacturer_mapping[vepl_part_no])
                        bom_line_item.save()
                    # print('final', vepl_to_references_mapping)
                    if vepl_part_no in vepl_to_references_mapping:
                        for ref in set(vepl_to_references_mapping[vepl_part_no]):
                            # print('current ref in loop ', ref)
                            BillOfMaterialsLineItemReference.objects.create(
                                name=ref, bom_line_item=bom_line_item, updated_by=user, created_by=user)
                            # reference = BillOfMaterialsLineItemReference.objects.filter(
                            #     name=ref).first()

                            # if reference:
                            #     print('got ref ', reference)
                            #     if reference.bom_line_item:
                            #         reference.bom_line_item = bom_line_item
                            #         reference.save()
                            #         print('saved ref ', reference)
                            #     else:
                            #         print(
                            #             'bom_line_item is None for reference ', reference)

                print('outside the loop , check if it reaches here')

            return 'Hardware BOM Uploaded Successfully'

        else:
            # Get the uploaded file
            pe_bom_file_data = pd.read_excel(
                bom_file, header=11, sheet_name='gen2_1600w_aux_supply')

            pe_bom_file_data.columns = [
                "Level", "VEPL Part No", "Priority Level", "Value", "PCB Footprint",
                "Type", "Description", "Mfr", "Mfr. Part No", "Customer Part No",
                "Qty", "Reference"
            ]

            # Drop rows that are completely empty
            # pe_bom_file_data.dropna(how='all', inplace=True)
            print('pe bom fiel first few rows', pe_bom_file_data.head())

            for index, row in pe_bom_file_data.iterrows():
                mfr_part_number = row['Mfr. Part No'] if pd.notna(
                    row['Mfr. Part No']) else None
                print(f"Index: {index}, Row: {row}")
                if mfr_part_number is not None:
                    # Update or create Manufacturer
                    print(f"Index: {index}, Row: {row}")

                    manufacturer_name = row['Mfr'] if pd.notna(
                        row['Mfr']) else None
                    manufacturer, updated = Manufacturer.objects.update_or_create(
                        name=manufacturer_name,
                        # Specify default values here if necessary
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        } if manufacturer_name is not None else None
                    )
                    # print(f"Manufacturer {'updated' if not updated else 'created'}: {manufacturer}")

                    # Create or get ManufacturerPart
                    mfr_part, updated = ManufacturerPart.objects.update_or_create(
                        part_number=mfr_part_number,
                        manufacturer=manufacturer,
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        }
                        if manufacturer_name is not None else None
                    )
                    # print(f"ManufacturerPart {'updated' if not updated else 'created'}: {mfr_part}")

                    # Create or get BillOfMaterialsLineItemType
                    line_item_type_name = row['Type'] if pd.notna(
                        row['Type']) else None
                    line_item_type, updated = BillOfMaterialsLineItemType.objects.update_or_create(
                        name=line_item_type_name,
                        # Specify default values here if necessary
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        }if line_item_type_name is not None else None
                    )
                    # print(f"BillOfMaterialsLineItemType {'updated' if not updated else 'created'}: {line_item_type}")

                    existing_bom_line_item = BillOfMaterialsLineItem.objects.filter(
                        bom=bom,
                        manufacturer_parts=mfr_part
                    ).first()

                    # Create or update BOM Line Item
                    if existing_bom_line_item:
                        # ManufacturerPart exists for this BOM Line Item, so update it
                        bom_line_item = existing_bom_line_item
                        bom_line_item.level = row['Level'] if pd.notna(
                            row['Level']) else None
                        bom_line_item.priority_level = row['Priority Level'] if pd.notna(
                            row['Priority Level']) else None
                        bom_line_item.value = row['Value'] if pd.notna(
                            row['Value']) else None
                        bom_line_item.pcb_footprint = row['PCB Footprint'] if pd.notna(
                            row['PCB Footprint']) else None
                        bom_line_item.line_item_type = line_item_type
                        bom_line_item.description = row['Description'] if pd.notna(
                            row['Description']) else None
                        bom_line_item.customer_part_number = row['Customer Part No'] if pd.notna(
                            row['Customer Part No']) else None
                        bom_line_item.quantity = int(
                            row['Qty']) if pd.notna(row['Qty']) else 0
                        bom_line_item.save()
                        print(f"BOM Line Item updated: {bom_line_item}")
                    else:
                        # ManufacturerPart doesn't exist for this BOM Line Item, so create it
                        bom_line_item = BillOfMaterialsLineItem.objects.create(
                            bom=bom,
                            level=row['Level'] if pd.notna(
                                row['Level']) else None,
                            priority_level=row['Priority Level'] if pd.notna(
                                row['Priority Level']) else None,
                            value=row['Value'] if pd.notna(
                                row['Value']) else None,
                            pcb_footprint=row['PCB Footprint'] if pd.notna(
                                row['PCB Footprint']) else None,
                            line_item_type=line_item_type,
                            description=row['Description'] if pd.notna(
                                row['Description']) else None,
                            customer_part_number=row['Customer Part No'] if pd.notna(
                                row['Customer Part No']) else None,
                            quantity=int(row['Qty']) if pd.notna(
                                row['Qty']) else 0,
                        )
                        # Add ManufacturerPart to the many-to-many relationship
                        bom_line_item.manufacturer_parts.add(mfr_part)
                        # print(f"BOM Line Item created: {bom_line_item}")

                    # Update or create BillOfMaterialsLineItemReference instances
                    references = row['Reference']
                    if references is not None:
                        for reference in str(references).split(','):
                            ref, updated = BillOfMaterialsLineItemReference.objects.update_or_create(
                                name=str(reference).strip(),
                                bom_line_item=bom_line_item,  # Include the BillOfMaterialsLineItem reference
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                            # print(f"BillOfMaterialsLineItemReference {'updated' if not updated else 'created'}: {ref}")
            return 'PE BOM Uploaded Successfully'

        # Read the Excel file directly from the file object

    except Exception as e:
        return ('BOM Upload Failed', 'FAILURE', str(e))


@shared_task
def process_bom_file_and_create_order(bom_file, bom_file_name, data, user_id):
    try:
        user = UserAccount.objects.get(pk=user_id)

        # file_path  = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
        bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

        product = Product.objects.get(id=data.get('product_id'))

        bom_type, _ = BillOfMaterialsType.objects.get_or_create(
            name=data.get('bom_type'),
            defaults={
                'updated_by': user,
                'created_by': user,
            })
        if (str(data.get('issue_date')) == ''):
            issue_date = timezone.now().date()
        else:
            issue_date = data.get('issue_date')

        bom, _ = BillOfMaterials.objects.get_or_create(
            product=product,
            bom_file_name=bom_file_name,
            bom_rev_number=data.get('bom_rev_no'),
            defaults={
                'bom_type': bom_type,
                'change_note': data.get('bom_rev_change_note'),
                'issue_date': issue_date,
                'bom_file': 'bom_files/' + bom_file_name,
                'updated_by': user,
                'created_by': user,
            })

        print('bom created')

        with transaction.atomic():
            bom_line_items_to_create = []
            vepl_to_manufacturer_mapping = {}
            vepl_to_references_mapping = {}
            for _, row in bom_file_data.iterrows():
                print('index', _)
                if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
                    vepl_part_no = row['VEPL Part No']

                    if pd.notnull(row['Mfr']):
                        parts = [str(part).strip()
                                 for part in str(row['Mfr']).split('\n') if str(part).strip()]
                        manufacturers = parts if not str(row['Mfr']).startswith(
                            '\n') else parts[1:]
                    else:
                        manufacturers = []

                    if pd.notnull(row['Mfr. Part No']):
                        parts = [str(part).strip()
                                 for part in str(row['Mfr. Part No']).split('\n') if str(part).strip()]
                        manufacturer_part_nos = parts if not str(row['Mfr. Part No']).startswith(
                            '\n') else parts[1:]
                    else:
                        manufacturer_part_nos = []

                    for mfr, mfr_part_no in zip(manufacturers, manufacturer_part_nos):
                        if str(mfr).strip() and str(mfr_part_no).strip():
                            manufacturer, _ = Manufacturer.objects.get_or_create(
                                name=str(mfr).strip(),
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                            manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                                part_number=str(mfr_part_no).strip(),
                                manufacturer=manufacturer,
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )

                            if vepl_part_no not in vepl_to_manufacturer_mapping:
                                vepl_to_manufacturer_mapping[vepl_part_no] = []

                            vepl_to_manufacturer_mapping[vepl_part_no].append(
                                manufacturer_part)

                    if 'Reference' in row and pd.notnull(row['Reference']):
                        for reference in str(row['Reference']).split(','):
                            ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
                                name=str(reference).strip(),
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                            if vepl_part_no not in vepl_to_references_mapping:
                                vepl_to_references_mapping[vepl_part_no] = []

                            vepl_to_references_mapping[vepl_part_no].append(
                                ref.name)

                    assembly_stage, _ = AssemblyStage.objects.get_or_create(
                        name=row.get('Assy Stage', None),
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        })
                    line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
                        name=str(row.get('Type')).strip().upper(),
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        })
                    checklist_item_type_value = ''
                    if (row.get('Type')):
                        if str(row.get('Type')).strip().upper() == 'PCB':
                            checklist_item_type_value = 'PCB'
                        elif str(row.get('Type')).strip().upper() == 'PCB SERIAL NUMBER LABEL':
                            checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER PASTE':
                            checklist_item_type_value = 'SOLDER PASTE'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER BAR':
                            checklist_item_type_value = 'SOLDER BAR'
                        elif str(row.get('Type')).strip().upper() == 'IPA':
                            checklist_item_type_value = 'IPA'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER FLUX':
                            checklist_item_type_value = 'SOLDER FLUX'
                        elif str(row.get('Type')).strip().upper() == 'SOLDER WIRE':
                            checklist_item_type_value = 'SOLDER WIRE'
                        elif str(row.get('Type')).strip().upper() == 'SMT PALLET':
                            checklist_item_type_value = 'SMT PALLET'
                        elif str(row.get('Type')).strip().upper() == 'WAVE PALLET':
                            checklist_item_type_value = 'WAVE PALLET'
                        else:
                            checklist_item_type_value = 'RAW MATERIAL'

                    checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
                        'updated_by': user,
                        'created_by': user,
                    })

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
                    uom = row['UOM'] if 'UOM' in row and pd.notnull(
                        row['UOM']) else ''
                    ecn = row['ECN'] if 'ECN' in row and pd.notnull(
                        row['ECN']) else ''
                    msl = row['MSL'] if 'MSL' in row and pd.notnull(
                        row['MSL']) else ''
                    remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
                        row['Remarks']) else ''

                    existing_item = BillOfMaterialsLineItem.objects.filter(
                        part_number=row['VEPL Part No'], bom=bom).first()

                    if existing_item:
                        existing_item.level = level
                        existing_item.priority_level = priority_level
                        existing_item.value = value
                        existing_item.pcb_footprint = pcb_footprint
                        existing_item.line_item_type = line_item_type
                        existing_item.description = description
                        existing_item.customer_part_number = customer_part_number
                        existing_item.quantity = quantity
                        existing_item.remarks = remarks
                        existing_item.uom = uom
                        existing_item.ecn = ecn
                        existing_item.msl = msl
                        existing_item.assembly_stage = assembly_stage
                        existing_item.updated_by = user
                        existing_item.created_by = user
                        if existing_item.part_number in vepl_to_manufacturer_mapping:
                            existing_item.manufacturer_parts.set(
                                vepl_to_manufacturer_mapping[vepl_part_no])

                        if existing_item.part_number in vepl_to_references_mapping:
                            reference = BillOfMaterialsLineItemReference.objects.filter(
                                name=vepl_to_references_mapping[vepl_part_no]).first()
                            if reference and reference.bom_line_item:
                                reference.bom_line_item = existing_item
                                reference.save()

                        existing_item.save()

                    else:
                        bom_line_items_to_create.append(BillOfMaterialsLineItem(
                            part_number=row['VEPL Part No'],
                            bom=bom,
                            level=level,
                            priority_level=priority_level,
                            value=value,
                            pcb_footprint=pcb_footprint,
                            line_item_type=line_item_type,
                            description=description,
                            customer_part_number=customer_part_number,
                            quantity=quantity,
                            remarks=remarks,
                            uom=uom,
                            ecn=ecn,
                            msl=msl,
                            assembly_stage=assembly_stage,
                            created_by=user,
                            updated_by=user
                        ))

            BillOfMaterialsLineItem.objects.bulk_create(
                bom_line_items_to_create)

            bom_line_items = BillOfMaterialsLineItem.objects.filter(bom=bom)
            for bom_line_item in bom_line_items:
                vepl_part_no = bom_line_item.part_number

                if vepl_part_no in vepl_to_manufacturer_mapping:
                    bom_line_item.manufacturer_parts.set(
                        vepl_to_manufacturer_mapping[vepl_part_no])
                    bom_line_item.save()

                if vepl_part_no in vepl_to_references_mapping:
                    for ref in vepl_to_references_mapping[vepl_part_no]:
                        reference = BillOfMaterialsLineItemReference.objects.filter(
                            name=ref).first()
                        if reference:
                            if reference.bom_line_item:
                                reference.bom_line_item = bom_line_item
                                reference.save()
                            # else:
                            #     current_task.logger.warning(
                            #         f"Warning: Bom line item not found for reference {ref_name}")
                        # else:
                        #     current_task.logger.warning(
                        #         f"Warning: Reference {ref} not found in the database.")
            # bom_items_serializer = BillOfMaterialsLineItemSerializer(bom.bom_line_items, many=True)

        order = Order.objects.create(
            bom=bom, batch_quantity=data.get('batch_quantity'), updated_by=user, created_by=user)

        return ('BOM Uploaded and Order Created Successfully', 'SUCCESS', None)

    except Exception as e:
        logger.info(f"Exception in process_bom_file task: {str(e)}")
        return ('BOM Upload Failed', 'FAILURE', str(e))


@shared_task
def process_bom_file_and_create_order_new(bom_file, bom_file_name, data, user_id):
    try:
        # Assuming 'user' is defined somewhere in your code

        # Get the uploaded file from the request
        user = UserAccount.objects.get(pk=user_id)
        bom_format_id = data.get('bom_format_id')
        bom_format = BomFormat.objects.get(
            pk=bom_format_id) if bom_format_id else None

        # Read the Excel file directly from the file object
        bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

        product = Product.objects.get(id=data.get('product_id'))

        bom_type, _ = BillOfMaterialsType.objects.get_or_create(
            name=data.get('bom_type'),
            defaults={
                'updated_by': user,
                'created_by': user,
            })

        if (str(data.get('issue_date')) == ''):
            issue_date = timezone.now().date()
        else:
            issue_date = data.get('issue_date')

        pcb_file_name = data.get('pcb_file_name')
        pcb_bbt_test_report_file = None
        if pcb_file_name:
            pcb_bbt_test_report_file = 'pcb_bbt_test_report_files/' + pcb_file_name

        bom, _ = BillOfMaterials.objects.get_or_create(
            product=product,
            bom_file_name=bom_file_name,
            bom_rev_number=data.get('bom_rev_no'),
            bom_format=bom_format,
            defaults={
                'bom_type': bom_type,
                'change_note': data.get('bom_rev_change_note'),
                'issue_date': issue_date,
                'pcb_file_name': pcb_file_name,
                'pcb_bbt_test_report_file': pcb_bbt_test_report_file,
                'bom_file': 'bom_files/' + bom_file_name,
                'updated_by': user,
                'created_by': user,
            })

        print('bom created')

        if bom_format is None or "Hardware Design" in bom.bom_format.name:

            print("NaN count before dropna:",
                  bom_file_data['VEPL Part No'].isnull().sum())
            bom_file_data = bom_file_data.dropna(subset=['VEPL Part No'])
            print("NaN count after dropna:",
                  bom_file_data['VEPL Part No'].isnull().sum())

            if not bom_file_data.empty:

                print("Before filtering - Row count:", len(bom_file_data))

                print(bom_file_data['VEPL Part No'])

                # bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
                #     'VEPL')]
                bom_file_data['VEPL Part No'] = bom_file_data['VEPL Part No'].astype(
                    str)

                bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.strip(
                ).str.startswith('VEPL')]

                print(bom_file_data['VEPL Part No'])

                print("After filtering - Row count:", len(bom_file_data))
                print("Filtered DataFrame:")
                print(bom_file_data)
            else:
                print("No rows left in DataFrame after dropping NaN values.")

            # Drop rows where 'vepl part' is NaN
            # bom_file_data = bom_file_data.dropna(subset=['VEPL Part No'])
            # bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
            #     'VEPL')]

            # Reset index after dropping rows
            bom_file_data.reset_index(drop=True, inplace=True)

            # Forward fill
            bom_file_data.ffill(inplace=True)

            # Lists to store instances and mapping

            with transaction.atomic():
                bom_line_items_to_create = []
                vepl_to_references_mapping = {}
                vepl_to_manufacturer_mapping = {}
                processed_part_numbers = set()

                # Iterate through rows in the DataFrame
                for _, row in bom_file_data.iterrows():
                    print('index', _)
                    if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
                        vepl_part_no = row['VEPL Part No']
                        # Handling 'Mfr' field
                        if ('Mfr' in row and pd.notnull(row['Mfr'])) or ('Manufacturer' in row and pd.notnull(row['Manufacturer'])):
                            mfr_name = str(
                                row.get('Mfr')).strip().replace('\n', '')
                            manufacturer, _ = Manufacturer.objects.get_or_create(
                                name=mfr_name,
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                    # Add other fields if needed
                                })
                        else:
                            manufacturer = None

                        # if pd.notnull(row['Mfr. Part No']):
                        #     mfr_part_no = str(row.get('Mfr. Part No')
                        #                       ).strip().replace('\n', '')
                        #     manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                        #         part_number=mfr_part_no,
                        #         manufacturer=manufacturer,
                        #         defaults={
                        #             'updated_by': user,
                        #             'created_by': user,

                        #         })

                        if pd.notnull(row.get('Mfr. Part No', None)) or pd.notnull(row.get('Mfr.Part No', None)):
                            mfr_part_no = str(row.get('Mfr. Part No', row.get(
                                'Mfr.Part No', ''))).strip().replace('\n', '')
                            # Check if either 'Mfr. Part No' or 'Mfr.Part No' column is not null
                            manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                                part_number=mfr_part_no,
                                manufacturer=manufacturer,
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                        else:
                            manufacturer_part = None

                        if vepl_part_no not in vepl_to_manufacturer_mapping:
                            vepl_to_manufacturer_mapping[vepl_part_no] = []

                        vepl_to_manufacturer_mapping[vepl_part_no].append(
                            manufacturer_part)

                        # Handling 'Reference' field
                        if 'Reference' in row and pd.notnull(row['Reference']):
                            # print('Entering Reference block for row:', row)
                            for reference in str(row['Reference']).split(','):
                                # ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
                                #     name=str(reference).strip(),
                                #     defaults={
                                #         'updated_by': user,
                                #         'created_by': user,
                                #     }
                                # )

                                if vepl_part_no not in vepl_to_references_mapping:
                                    vepl_to_references_mapping[vepl_part_no] = [
                                    ]

                                vepl_to_references_mapping[vepl_part_no].append(
                                    str(reference.strip()))
                        # print('vepl_to_references_mapping in loop',vepl_to_references_mapping)

                        assembly_stage, _ = AssemblyStage.objects.get_or_create(
                            name=row.get('Assy Stage', None),
                            defaults={
                                'updated_by': user,
                                'created_by': user,
                            })
                        line_item_type, _ = BillOfMaterialsLineItemType.objects.get_or_create(
                            name=str(row.get('Type')).strip().upper(),
                            defaults={
                                'updated_by': user,
                                'created_by': user,
                            })

                        checklist_item_type_value = ''
                        if (row.get('Type')):
                            if str(row.get('Type')).strip().upper() == 'PCB':
                                checklist_item_type_value = 'PCB'
                            elif str(row.get('Type')).strip().upper() == 'PCB SERIAL NUMBER LABEL':
                                checklist_item_type_value = 'PCB SERIAL NUMBER LABEL'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER PASTE':
                                checklist_item_type_value = 'SOLDER PASTE'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER BAR':
                                checklist_item_type_value = 'SOLDER BAR'
                            elif str(row.get('Type')).strip().upper() == 'IPA':
                                checklist_item_type_value = 'IPA'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER FLUX':
                                checklist_item_type_value = 'SOLDER FLUX'
                            elif str(row.get('Type')).strip().upper() == 'SOLDER WIRE':
                                checklist_item_type_value = 'SOLDER WIRE'
                            elif str(row.get('Type')).strip().upper() == 'SMT PALLET':
                                checklist_item_type_value = 'SMT PALLET'
                            elif str(row.get('Type')).strip().upper() == 'WAVE PALLET':
                                checklist_item_type_value = 'WAVE PALLET'
                            else:
                                checklist_item_type_value = 'RAW MATERIAL'

                        checklist_item_type, _ = ChecklistItemType.objects.get_or_create(name=checklist_item_type_value, defaults={
                            'updated_by': user,
                            'created_by': user,
                        })

                        level = row['Level'] if 'Level' in row and pd.notnull(
                            row['Level']) else ''
                        priority_level = row.get('Prioprity Level') if 'Prioprity Level' in row and pd.notnull(
                            row['Prioprity Level']) else \
                            row.get('Priority Level') if 'Priority Level' in row and pd.notnull(
                                row['Priority Level']) else ''
                        value = row['Value'] if 'Value' in row and pd.notnull(
                            row['Value']) else ''
                        pcb_footprint = row['PCB Footprint'] if 'PCB Footprint' in row and pd.notnull(
                            row['PCB Footprint']) else ''
                        description = row['Description'] if 'Description' in row and pd.notnull(
                            row['Description']) else \
                            row.get('Description/part') if 'Description/part' in row and pd.notnull(
                                row['Description/part']) else ''
                        customer_part_number = row['Customer Part No'] if 'Customer Part No' in row and pd.notnull(
                            row['Customer Part No']) else ''

                        quantity_column_names = [
                            'Qty/ Product', 'Qty/Product', 'Quantity']

                        # Loop through possible column names to find the quantity
                        for qty_col_name in quantity_column_names:
                            if qty_col_name in row and pd.notnull(row[qty_col_name]):
                                quantity = row[qty_col_name]
                                break
                        else:
                            quantity = 0

                        # quantity = row['Qty/ Product'] if 'Qty/ Product' in row and pd.notnull(
                        #     row['Qty/ Product']) else 0

                        uom = row['UOM'] if 'UOM' in row and pd.notnull(
                            row['UOM']) else ''
                        ecn = row['ECN'] if 'ECN' in row and pd.notnull(
                            row['ECN']) else ''
                        msl = row['MSL'] if 'MSL' in row and pd.notnull(
                            row['MSL']) else ''
                        remarks = row['Remarks'] if 'Remarks' in row and pd.notnull(
                            row['Remarks']) else ''

                        existing_item = BillOfMaterialsLineItem.objects.filter(
                            part_number=row['VEPL Part No'], bom=bom).first()

                        if existing_item:
                            existing_item.level = level
                            existing_item.priority_level = priority_level
                            existing_item.value = value
                            existing_item.pcb_footprint = pcb_footprint
                            existing_item.line_item_type = line_item_type
                            existing_item.description = description
                            existing_item.customer_part_number = customer_part_number
                            existing_item.quantity = quantity
                            existing_item.remarks = remarks
                            existing_item.uom = uom
                            existing_item.ecn = ecn
                            existing_item.msl = msl
                            existing_item.assembly_stage = assembly_stage
                            existing_item.updated_by = user
                            existing_item.created_by = user

                            if existing_item.part_number in vepl_to_references_mapping:
                                existing_references = BillOfMaterialsLineItemReference.objects.filter(
                                    name=vepl_to_references_mapping[vepl_part_no], bom_line_item=existing_item)
                                if existing_references:
                                    pass
                                else:
                                    BillOfMaterialsLineItemReference.objects.create(
                                        name=vepl_to_references_mapping[vepl_part_no], bom_line_item=existing_item, updated_by=user, created_by=user)

                            if existing_item.part_number in vepl_to_manufacturer_mapping:
                                existing_item.manufacturer_parts.set(
                                    vepl_to_manufacturer_mapping[vepl_part_no])
                            existing_item.save()

                        else:

                            # Other fields handling...
                            # Create BillOfMaterialsLineItem instance
                            # print('if not an existing item')
                            bom_line_item = BillOfMaterialsLineItem(
                                part_number=row['VEPL Part No'],
                                bom=bom,
                                level=level,
                                priority_level=priority_level,
                                value=value,
                                pcb_footprint=pcb_footprint,
                                line_item_type=line_item_type,
                                description=description,
                                customer_part_number=customer_part_number,
                                quantity=quantity,
                                remarks=remarks,
                                uom=uom,
                                ecn=ecn,
                                msl=msl,
                                assembly_stage=assembly_stage,
                                created_by=user,
                                updated_by=user
                            )
                            bom_line_items_to_create.append(bom_line_item)
                            dupli_count = 0
                            for bom_line_item in bom_line_items_to_create:
                                if bom_line_item.part_number == row['VEPL Part No']:
                                    dupli_count += 1
                                    print(
                                        str(bom_line_item.part_number) + 'exists')
                            if dupli_count > 1:
                                # print('dupli count exceeded')
                                bom_line_items_to_create.remove(bom_line_item)

                BillOfMaterialsLineItem.objects.bulk_create(
                    bom_line_items_to_create)

                bom_line_items = BillOfMaterialsLineItem.objects.filter(
                    bom=bom)
                for bom_line_item in bom_line_items:
                    vepl_part_no = bom_line_item.part_number
                    if vepl_part_no in vepl_to_manufacturer_mapping:
                        bom_line_item.manufacturer_parts.set(
                            vepl_to_manufacturer_mapping[vepl_part_no])
                        bom_line_item.save()
                    # print('final', vepl_to_references_mapping)
                    if vepl_part_no in vepl_to_references_mapping:
                        for ref in set(vepl_to_references_mapping[vepl_part_no]):
                            # print('current ref in loop ', ref)
                            BillOfMaterialsLineItemReference.objects.create(
                                name=ref, bom_line_item=bom_line_item, updated_by=user, created_by=user)
                            # reference = BillOfMaterialsLineItemReference.objects.filter(
                            #     name=ref).first()
                            # if reference:
                            #     print('got ref ', reference)
                            #     if reference:
                            #         reference.bom_line_item = bom_line_item
                            #         reference.save()
                            #         print('saved ref ', reference)

            return ('BOM Uploaded and Order Created Successfully', 'SUCCESS', None)

        else:
            print('inside else ')
            pe_bom_file_data = pd.read_excel(
                bom_file, header=11, sheet_name='gen2_1600w_aux_supply')

            pe_bom_file_data.columns = [
                "Level", "VEPL Part No", "Priority Level", "Value", "PCB Footprint",
                "Type", "Description", "Mfr", "Mfr. Part No", "Customer Part No",
                "Qty", "Reference"
            ]

            # Drop rows that are completely empty
            # pe_bom_file_data.dropna(how='all', inplace=True)
            # print('pe bom fiel first few rows', pe_bom_file_data.head())

            for index, row in pe_bom_file_data.iterrows():
                mfr_part_number = row['Mfr. Part No'] if pd.notna(
                    row['Mfr. Part No']) else None
                # print(f"Index: {index}, Row: {row}")
                if mfr_part_number is not None:
                    # Update or create Manufacturer
                    print(f"Index: {index}, Row: {row}")

                    manufacturer_name = row['Mfr'] if pd.notna(
                        row['Mfr']) else None
                    manufacturer, updated = Manufacturer.objects.update_or_create(
                        name=manufacturer_name,
                        # Specify default values here if necessary
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        } if manufacturer_name is not None else None
                    )
                    # print(f"Manufacturer {'updated' if not updated else 'created'}: {manufacturer}")

                    # Create or get ManufacturerPart
                    mfr_part, updated = ManufacturerPart.objects.update_or_create(
                        part_number=mfr_part_number,
                        manufacturer=manufacturer,
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        }
                        if manufacturer_name is not None else None
                    )
                    # print(f"ManufacturerPart {'updated' if not updated else 'created'}: {mfr_part}")

                    # Create or get BillOfMaterialsLineItemType
                    line_item_type_name = row['Type'] if pd.notna(
                        row['Type']) else None
                    line_item_type, updated = BillOfMaterialsLineItemType.objects.update_or_create(
                        name=line_item_type_name,
                        # Specify default values here if necessary
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                        }if line_item_type_name is not None else None
                    )
                    # print(f"BillOfMaterialsLineItemType {'updated' if not updated else 'created'}: {line_item_type}")

                    existing_bom_line_item = BillOfMaterialsLineItem.objects.filter(
                        bom=bom,
                        manufacturer_parts=mfr_part
                    ).first()

                    # Create or update BOM Line Item
                    if existing_bom_line_item:
                        # ManufacturerPart exists for this BOM Line Item, so update it
                        bom_line_item = existing_bom_line_item
                        bom_line_item.level = row['Level'] if pd.notna(
                            row['Level']) else None
                        bom_line_item.priority_level = row['Priority Level'] if pd.notna(
                            row['Priority Level']) else None
                        bom_line_item.value = row['Value'] if pd.notna(
                            row['Value']) else None
                        bom_line_item.pcb_footprint = row['PCB Footprint'] if pd.notna(
                            row['PCB Footprint']) else None
                        bom_line_item.line_item_type = line_item_type
                        bom_line_item.description = row['Description'] if pd.notna(
                            row['Description']) else None
                        bom_line_item.customer_part_number = row['Customer Part No'] if pd.notna(
                            row['Customer Part No']) else None
                        bom_line_item.quantity = int(
                            row['Qty']) if pd.notna(row['Qty']) else 0
                        bom_line_item.save()
                        print(f"BOM Line Item updated: {bom_line_item}")
                    else:
                        # ManufacturerPart doesn't exist for this BOM Line Item, so create it
                        bom_line_item = BillOfMaterialsLineItem.objects.create(
                            bom=bom,
                            level=row['Level'] if pd.notna(
                                row['Level']) else None,
                            priority_level=row['Priority Level'] if pd.notna(
                                row['Priority Level']) else None,
                            value=row['Value'] if pd.notna(
                                row['Value']) else None,
                            pcb_footprint=row['PCB Footprint'] if pd.notna(
                                row['PCB Footprint']) else None,
                            line_item_type=line_item_type,
                            description=row['Description'] if pd.notna(
                                row['Description']) else None,
                            customer_part_number=row['Customer Part No'] if pd.notna(
                                row['Customer Part No']) else None,
                            quantity=int(row['Qty']) if pd.notna(
                                row['Qty']) else 0,
                        )
                        # Add ManufacturerPart to the many-to-many relationship
                        bom_line_item.manufacturer_parts.add(mfr_part)
                        # print(f"BOM Line Item created: {bom_line_item}")

                    # Update or create BillOfMaterialsLineItemReference instances
                    references = row['Reference']
                    if references is not None:
                        for reference in str(references).split(','):
                            ref, updated = BillOfMaterialsLineItemReference.objects.update_or_create(
                                name=str(reference).strip(),
                                bom_line_item=bom_line_item,  # Include the BillOfMaterialsLineItem reference
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
                            # print(f"BillOfMaterialsLineItemReference {'updated' if not updated else 'created'}: {ref}")
            # return 'PE BOM Uploaded Successfully'

        order = Order.objects.create(
            bom=bom, batch_quantity=data.get('batch_quantity'), updated_by=user, created_by=user)

        print('order created succesfully', order)
        store_team_profiles = UserAccount.objects.filter(
            is_store_team=True)

        # Serialize the queryset using a serializer
        store_team_profiles_serializer = UserAccountSerializer(
            store_team_profiles, many=True).data
        # print(store_team_profiles_serializer)
        # print('sending mail task started')
        send_order_creation_mail.delay(
            order.id, store_team_profiles_serializer)

        return ('BOM Uploaded and Order Created Successfully', 'SUCCESS', None)

    except Exception as e:
        return ('BOM Upload Failed', 'FAILURE', str(e))


# @shared_task
# def send_order_creation_mail(order, store_team_profiles):

#     for profile in store_team_profiles:
#         subject = 'Order Creation Notification'
#         sender_email = order.created_by.email
#         sender_name = str(order.created_by.first_name) + \
#             str(order.created_by.last_name)

#         context = {
#             'project': order.bom.product.project.name,
#             'product': order.bom.product.name,
#             'batch_quantity': order.batch_quantity,
#             'website_link': 'https://sfcs.xtractautomation.com/checklist',
#             'created_by': sender_name,
#             'profile': profile,
#         }
#         html_message = render_to_string('order_creation_mail.html', context)
#         plain_message = strip_tags(html_message)

#         email_from = f'{sender_name} <{sender_email}>'

#         # recipient_list = [
#         #     satvikkatoch@velankanigroup.com
#         # ]

#         send_mail(subject, plain_message, email_from,
#                   [profile.email], html_message=html_message)


# @shared_task
# def send_order_creation_mail(order_id, store_team_profiles):
#     try:
#         # Fetch the Order object based on the provided order_id
#         order = Order.objects.get(id=order_id)

#         for profile in store_team_profiles:
#             subject = 'Order Creation Notification'
#             sender_email = order.created_by.email
#             sender_name = str(order.created_by.first_name) + \
#                 str(order.created_by.last_name)

#             context = {
#                 'project': order.bom.product.project.name,
#                 'product': order.bom.product.name,
#                 'batch_quantity': order.batch_quantity,
#                 'website_link': 'https://sfcs.xtractautomation.com/checklist',
#                 'created_by': sender_name,
#                 'profile': profile,
#             }
#             html_message = render_to_string(
#                 'order_creation_email.html', context)
#             plain_message = strip_tags(html_message)

#             email_from = f'{sender_name} <{sender_email}>'

#             # recipient_list = [
#             #     satvikkatoch@velankanigroup.com
#             # ]

#             send_mail(subject, plain_message, email_from,
#                       [profile], html_message=html_message)

#     except Order.DoesNotExist:
#         # Handle the case where the Order with the provided order_id does not exist
#         pass

@shared_task
def send_order_creation_mail(order_id, store_team_profiles):
    try:
        # Fetch the Order object based on the provided order_id
        print('inside mail task')
        order = Order.objects.get(id=order_id)

        for profile_data in store_team_profiles:
            subject = 'Order Creation Notification'
            # sender_email = order.created_by.email
            # sender_name = str(order.created_by.first_name) + \
            #     str(order.created_by.last_name)
            created_by = f"{order.created_by.first_name} {order.created_by.last_name}"

            context = {
                'project': order.bom.product.project.name,
                'product': order.bom.product.name,
                'batch_quantity': order.batch_quantity,
                'website_link': 'https://sfcs.xtractautomation.com/checklist',
                'created_by': created_by,
                'profile': profile_data,
            }
            html_message = render_to_string(
                'order_creation_email.html', context)
            plain_message = strip_tags(html_message)

            sender_email = settings.EMAIL_HOST_USER
            sender_name = 'Velankani SFCS'
            email_from = f'{sender_name} <{sender_email}>'

            # recipient_list = [
            #     satvikkatoch@velankanigroup.com
            # ]

            send_mail(subject, plain_message, email_from,
                      [profile_data['email']], html_message=html_message)

            print(f"Order creation email sent to {profile_data['email']}")

    except Order.DoesNotExist:
        # Handle the case where the Order with the provided order_id does not exist
        pass
