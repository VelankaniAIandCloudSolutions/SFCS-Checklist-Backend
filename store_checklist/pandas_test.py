
import os
import pandas as pd


# def read_and_print_excel(file_path):
#     # Read the Excel file
#     bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)


#     bom_file_data.ffill(inplace=True)

#     output_file_path = "output.xlsx"  # Specify the desired output file path
#     bom_file_data.to_excel(output_file_path, index=False)

#     print(f'Data has been written to {output_file_path}')
#     # # Create a new DataFrame to store the expanded rows
#     expanded_rows = []

#     # Iterate over the rows in the original DataFrame
#     for _, row in bom_file_data.head(10).iterrows():
#         vepl_part_no = str(row['VEPL Part No']).strip()
#         description = str(row['Description']).strip()
#         manufacturer = str(row['Mfr']).strip()
#         manufacturer_part_no = str(row['Mfr. Part No']).strip()

#         # If there are multiple values, create a new row for each combination of values
#         if '\n' in vepl_part_no:
#             vepl_part_nos = vepl_part_no.split('\n')
#             descriptions = description.split('\n')
#             manufacturers = manufacturer.split('\n')
#             manufacturer_part_nos = manufacturer_part_no.split('\n')

#             # Check if the number of values after splitting is consistent
#             min_len = min(len(vepl_part_nos), len(descriptions),
#                           len(manufacturers), len(manufacturer_part_nos))

#             for i in range(min_len):
#                 new_row = row.copy()
#                 new_row['VEPL Part No'] = vepl_part_nos[i]
#                 new_row['Description'] = descriptions[i]
#                 new_row['Mfr'] = manufacturers[i]
#                 new_row['Mfr. Part No'] = manufacturer_part_nos[i]
#                 expanded_rows.append(new_row)
#         else:
#             # If there is only one value in the 'VEPL Part No' column, the entire row is copied and added to the expanded_rows list.
#             expanded_row = row.copy()
#             expanded_rows.append(expanded_row)

#     # Create a new DataFrame from the expanded rows
#     expanded_df = pd.DataFrame(expanded_rows)

#     # Reset index
#     expanded_df.reset_index(drop=True, inplace=True)

#     # Print the expanded DataFrame
#     # print(expanded_df)
#     columns_to_print = [
#         "VEPL Part No", "Value", "Description", "Mfr", 'Mfr. Part No']
#     print(expanded_df[columns_to_print])


# if __name__ == "__main__":
#     # Assuming your script is in the 'store_checklist' directory
#     current_directory = os.path.dirname(__file__)

#     # Construct the full file path using os.path.join()
#     file_path = os.path.join(
#         current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

#     read_and_print_excel(file_path)


# import os
# import pandas as pd


# def read_and_parse(file_path):
#     # Read the Excel file
#     # Read the Excel file
#     bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)

#     # Initialize variables to store previous Sl no. and VEPL Part No
#     # prev_sl_no = None
#     # prev_vepl_part_no = None

#     # Iterate through the rows
#     for index, row in bom_file_data.head(6).iterrows():
#         # Check if Sl no. is not null
#         # if pd.notna(row['Sl no.']):
#         # # Extract values from the current row
#         # level = row['Level']
#         # vepl_part_no = row['VEPL Part No']
#         # prioprity_level = row['Prioprity Level']
#         # type = row['Type']
#         # description = row['Description']
#         # manufacturer_name = row['Mfr']
#         # value = row['Value']
#         # pcb_footprint = row['PCB Footprint']
#         # line_item_type = row['Type']  # Adjust this based on your data
#         # description = row['Description']

#         # bom_line_item = BillOfMaterialsLineItem(
#         #     level=level,
#         #     part_number=vepl_part_no,
#         #     priority_level=priority_level,
#         #     value=value,
#         #     pcb_footprint=pcb_footprint,
#         #     line_item_type=line_item_type,
#         #     description=description,
#         #     manufacturer_name=manufacturer_name,

#         # )
#         # else:
#         # print(row['VEPL Part No'])
#         if index == 4:
#             result = bom_file_data[bom_file_data['VEPL Part No']
#                                    == row['VEPL Part No']]
#             print(result)
#             print(result.iloc[0]['Type'])
#             type  = result.iloc[0]['Type']
#             mfr  = row['Mfr']


#         # bom_line_item.save()
# if __name__ == "__main__":
#     current_directory = os.path.dirname(__file__)
#     file_path = os.path.join(
#         current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

#     read_and_print_excel(file_path)


import os
import pandas as pd


def read_and_print_excel(file_path):
    # Read the Excel file
    bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)

    # Drop rows where 'vepl part' is NaN
    bom_file_data = bom_file_data.dropna(subset=['VEPL Part No'])
    bom_file_data = bom_file_data[bom_file_data['VEPL Part No'].str.startswith(
        'VEPL')]

    # Reset index after dropping rows
    bom_file_data.reset_index(drop=True, inplace=True)
    # forward fill
    bom_file_data.ffill(inplace=True)

    # Print the DataFrame
    print(bom_file_data)
    
    bom_line_items_to_create = []
    vepl_to_references_mapping = {}

    for _, row in bom_file_data.iterrows():
        if str(row['VEPL Part No']) != 'nan' and str(row['VEPL Part No']).strip().startswith('VEPL'):
            vepl_part_no = row['VEPL Part No']
            
            if pd.notnull(row['Mfr']):
                mfr_name = str(row.get('Mfr')).strip().replace('\n', '')
                  manufacturer, _ = Manufacturer.objects.get_or_create(
                        name=mfr_name,
                        defaults={
                            'updated_by': user,
                            'created_by': user,
                            # Add other fields if needed
                        })
            else:
                manufacturer=None
                
             
            if pd.notnull(row['Mfr. Part No']):
                
                mfr_part_no = str(row.get('Mfr. Part No')).strip().replace('\n', '')
                manufacturer_part, _ = ManufacturerPart.objects.get_or_create(
                    name=mfr_part_no,
                    manufacturer=manufacturer,
                    defaults={
                        'updated_by': user,
                        'created_by': user,
                        'manufacturer': mfr,

                    })
            else:
                manufacturer_part=[]
                
            
              
                
            if 'Reference' in row and pd.notnull(row['Reference']):
                        for reference in str(row['Reference']).split(','):
                            ref, _ = BillOfMaterialsLineItemReference.objects.get_or_create(
                                name=str(reference).strip(),
                                defaults={
                                    'updated_by': user,
                                    'created_by': user,
                                }
                            )
             

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



if __name__ == "__main__":
    # Assuming your script is in the 'store_checklist' directory
    current_directory = os.path.dirname(__file__)

    # Construct the full file path using os.path.join()
    file_path = os.path.join(
        current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

    read_and_print_excel(file_path)
