

# def read_and_print_excel(file_path):
#     # Read the Excel file
#     bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)
#     bom_file_data.ffill(inplace=True)

#     # Create a new DataFrame to store the expanded rows
#     expanded_rows = []

#     # Iterate over the rows in the original DataFrame
#     for _, row in bom_file_data.head(6).iterrows():
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
#             expanded_row = row.copy()
#             expanded_rows.append(expanded_row)

#     # Create a new DataFrame from the expanded rows
#     expanded_df = pd.DataFrame(expanded_rows)

#     # Reset index
#     expanded_df.reset_index(drop=True, inplace=True)

#     # Print the expanded DataFrame
#     print(expanded_df)


# if __name__ == "__main__":
#     # Assuming your script is in the 'store_checklist' directory
#     current_directory = os.path.dirname(__file__)

#     # Construct the full file path using os.path.join()
#     file_path = os.path.join(
#         current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

#     read_and_print_excel(file_path)


# import os
# import pandas as pd
# import re


# def extract_manufacturer(text):
#     # Use regular expression to extract text between parentheses
#     match = re.search(r'\((.*?)\)', text)
#     return match.group(1) if match else text.strip()


# def read_and_print_excel(file_path):
#     # Read the Excel file into a DataFrame
#     df = pd.read_excel(file_path)

#     # Create a new DataFrame to store the expanded rows
#     expanded_rows = []

#     # Iterate through each row in the original DataFrame
#     for index, row in df.iterrows():
#         # Check if "Manufacturer" contains multiple rows
#         if pd.notna(row['Mfr']) and '\n' in str(row['Mfr']):
#             # Split the row based on new lines in "Manufacturer"
#             manufacturers = str(row['Mfr']).split('\n')

#             # Create new rows for each manufacturer
#             for m in manufacturers:
#                 new_row = row.copy()
#                 new_row['Mfr'] = m.strip()
#                 expanded_rows.append(new_row)
#         else:
#             # If no line breaks or NaN, keep the original row
#             expanded_rows.append(row)

#     # Create a new DataFrame from the expanded rows
#     expanded_df = pd.DataFrame(expanded_rows)

#     # Reset index for the new DataFrame
#     expanded_df.reset_index(drop=True, inplace=True)

#     print(expanded_df)


# if __name__ == "__main__":
#     # Assuming your script is in the 'store_checklist' directory
#     current_directory = os.path.dirname(__file__)

#     # Construct the full file path using os.path.join()
#     file_path = os.path.join(
#         current_directory, '../media/bom_files/test_book_3_rows_cloumns_till_manufactuer.xlsx')

#     read_and_print_excel(file_path)


# def read_and_print_excel(file_path):
#     # Read the Excel file
#     bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)

#     for _, row in bom_file_data.head(6).iterrows():
#         print(row)

#         # vepl_part_no = str(row['VEPL Part No']).strip()
#         # description = str(row['Description']).strip()
#         # manufacturer = str(row['Mfr']).strip()
#         # manufacturer_part_no = str(row['Mfr. Part No']).strip()


# if __name__ == "__main__":
#     # Assuming your script is in the 'store_checklist' directory
#     current_directory = os.path.dirname(__file__)

#     # Construct the full file path using os.path.join()
#     file_path = os.path.join(
#         current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

#     read_and_print_excel(file_path)


# def read_and_save_to_database(file_path):
#     # Assuming Django models are properly imported and defined

#     # Read the Excel file
#     bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)

#     # Initialize variables to store the last valid values
#     last_sn = None
#     last_level = None
#     last_vepl_part_no = None
#     last_priority_level = None

#     for _, row in bom_file_data.iterrows():
#         # Check if 'Sl no.' is NaN
#         if pd.isna(row['Sl no.']):
#             # Assign the 'Sl no.' based on the last valid 'Sl no.'
#             if pd.notna(row['VEPL Part No.']):
#                 # Case 1: 'VEPL Part No.' is present, assign the 'Sl no.' from the last valid row
#                 sno = last_sn
#             elif pd.notna(last_vepl_part_no):
#                 # Case 2: 'VEPL Part No.' is None, but last valid 'VEPL Part No.' is present
#                 # Assign the 'Sl no.' from the last valid row with the same 'VEPL Part No.'
#                 sno = last_sn
#             else:
#                 # Case 3: Both 'VEPL Part No.' and last valid 'VEPL Part No.' are None
#                 # Assign the 'Sl no.' from the last valid row
#                 sno = last_sn
#         else:
#             # Use the current 'Sl no.' if not NaN
#             sno = row['Sl no.']

#         # Assign other values based on the current row or the last valid row
#         level = row['Level'] if pd.notna(row['Level']) else last_level
#         vepl_part_no = row['VEPL Part No']
#         priority_level = row['Priority Level'] if pd.notna(
#             row['Priority Level']) else last_priority_level
#         value = row['Value']
#         pcb_footprint = row['PCB Footprint']
#         line_item_type = row['Type']  # Adjust this based on your data
#         description = row['Description']
#         # Extract manufacturer from 'Manufacturer' field
#         manufacturer_name = extract_manufacturer(row['Manufacturer'])
#         # Save or process the current row with the updated values
#         bom_line_item = BillOfMaterialsLineItem(
#             level=level,
#             part_number=vepl_part_no,
#             priority_level=priority_level,
#             value=value,
#             pcb_footprint=pcb_footprint,
#             line_item_type=line_item_type,
#             description=description,
#             manufacturer_name=manufacturer_name,
#             # ... other fields ...
#         )
#         bom_line_item.save()

#         # Update the last valid values
#         last_sn = sno
#         last_level = level
#         last_vepl_part_no = vepl_part_no
#         last_priority_level = priority_level
import os
import pandas as pd


def read_and_save_to_database(file_path):
    # Read the Excel file
    # Read the Excel file
    bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)

    # Initialize variables to store previous Sl no. and VEPL Part No
    prev_sl_no = None
    prev_vepl_part_no = None

    # Iterate through the rows
    for index, row in bom_file_data.head(6).iterrows():
        # Check if Sl no. is not null
        if pd.notna(row['Sl no.']):
            current_sl_no = row['Sl no.']
            prev_sl_no = current_sl_no  # Update previous Sl no.

        # Check if VEPL Part No changes
        if row['VEPL Part No'] != prev_vepl_part_no:
            prev_sl_no = None  # Reset previous Sl no.

        # Fill NaN values in the current row with values from the previous row
        bom_file_data.at[index, 'Sl no.'] = prev_sl_no

        # Print the row
        print(row)

        # Update previous VEPL Part No
        prev_vepl_part_no = row['VEPL Part No']


if __name__ == "__main__":
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(
        current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

    read_and_save_to_database(file_path)
