from celery import current_task, shared_task
import pandas as pd
from django.db import transaction
from .models import *
from accounts.models import UserAccount
from .serializers import BillOfMaterialsLineItemSerializer
from django.utils import timezone


@shared_task
def test_func(x, y):
    return x + y


@shared_task
def process_bom_file(bom_file, bom_file_name, data, user_id):
    try:
        user = UserAccount.objects.get(pk=user_id)

        # file_path  = 'media/PRYSM-Gen4_SERVER_BOM_20231120.xlsx'
        bom_file_data = pd.read_excel(bom_file, header=5, sheet_name=1)

        product, _ = Product.objects.get_or_create(
            name=data.get('product_name'),
            product_code=data.get('product_code'),
            defaults={
                'product_rev_number': data.get('product_rev_no'),
                'updated_by': user,
                'created_by': user,
            }
        )

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
                if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
                    vepl_part_no = row['VEPL Part No']

                    if pd.notnull(row['Mfr']):
                        parts = [str(part).strip()
                                 for part in row['Mfr'].split('\n') if str(part).strip()]
                        manufacturers = parts if not row['Mfr'].startswith(
                            '\n') else parts[1:]
                    else:
                        manufacturers = []

                    if pd.notnull(row['Mfr. Part No']):
                        parts = [str(part).strip()
                                 for part in row['Mfr. Part No'].split('\n') if str(part).strip()]
                        manufacturer_part_nos = parts if not row['Mfr. Part No'].startswith(
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
                        for reference in row['Reference'].split(','):
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
                        reference.bom_line_item = bom_line_item
                        reference.save()
            print(bom_line_items.first().id)
            # bom_items_serializer = BillOfMaterialsLineItemSerializer(bom.bom_line_items, many=True)

        return 'BOM Uploaded  and Order Created Successfully'

    except Exception as e:
        print(e)
        return 'BOM Upload Failed'


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
            issue_date=issue_date,
            bom_file_name=bom_file_name,
            defaults={
                'bom_type': bom_type,
                'bom_rev_number': data.get('bom_rev_no'),
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
                if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
                    vepl_part_no = row['VEPL Part No']

                    if pd.notnull(row['Mfr']):
                        parts = [str(part).strip()
                                 for part in row['Mfr'].split('\n') if str(part).strip()]
                        manufacturers = parts if not row['Mfr'].startswith(
                            '\n') else parts[1:]
                    else:
                        manufacturers = []

                    if pd.notnull(row['Mfr. Part No']):
                        parts = [str(part).strip()
                                 for part in row['Mfr. Part No'].split('\n') if str(part).strip()]
                        manufacturer_part_nos = parts if not row['Mfr. Part No'].startswith(
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
                        for reference in row['Reference'].split(','):
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
                            else:
                                current_task.logger.warning(
                                    f"Warning: Bom line item not found for reference {ref_name}")
                        else:
                            current_task.logger.warning(
                                f"Warning: Reference {ref} not found in the database.")
            # bom_items_serializer = BillOfMaterialsLineItemSerializer(bom.bom_line_items, many=True)

        order = Order.objects.create(
            bom=bom, batch_quantity=data.get('batch_quantity'), updated_by=user, created_by=user)

        return ('BOM Uploaded and Order Created Successfully', 'SUCCESS', None)

    except Exception as e:
        print(e)
        return ('BOM Upload Failed', 'FAILURE', str(e))
