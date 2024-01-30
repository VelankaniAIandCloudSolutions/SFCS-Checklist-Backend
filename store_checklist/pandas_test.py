# test_script.py
import os
import pandas as pd
from django.db import transaction


def read_and_print_excel(file_path):
    bom_file_data = pd.read_excel(file_path, header=5, sheet_name=1)
    # print(bom_file_data.head())

    bom_line_items_to_create = []
    vepl_to_manufacturer_mapping = {}
    vepl_to_references_mapping = {}
    for _, row in bom_file_data.head().iterrows():
        print("Current Row:", row)

    # Check if 'VEPL Part No' is not null
    # if pd.notnull(row['VEPL Part No']):
    #     vepl_part_nos = [vepl.strip()
    #                      for vepl in str(row['VEPL Part No']).split('\n')]
    #     print(f"Processing 'VEPL Part No' values: {vepl_part_nos}")

    #     # Check if 'Mfr' is not null
    #     if pd.notnull(row['Mfr']):
    #         manufacturers = [mfr.strip()
    #                          for mfr in str(row['Mfr']).split('\n')]
    #         print(f"  - Associated 'Mfr' values: {manufacturers}")


if __name__ == "__main__":
    # Assuming your script is in the 'store_checklist' directory
    current_directory = os.path.dirname(__file__)

    # Construct the full file path using os.path.join()
    file_path = os.path.join(
        current_directory, '../media/bom_files/PRYSM-Gen2_PTH_SERVER BOM(SIMM SERVER) (1).xlsx')

    read_and_print_excel(file_path)
