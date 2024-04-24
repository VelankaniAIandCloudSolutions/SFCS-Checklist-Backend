from datetime import datetime
import pandas as pd


def parse_spi_log_file(file_path):
    try:
        data = pd.read_csv(file_path, header=0)
        print(data.head(0))  # Print the first row to verify data reading
        board_serial_number = data.loc[0, 'BarCode'].strip('<>')
        print(f"Board Serial Number: {board_serial_number}")

        begin_date_time_str = data.loc[0, 'Date'] + \
            ' ' + data.loc[0, 'StartTime']

        end_date_time_str = data.loc[0, 'Date'] + ' ' + data.loc[0, 'EndTime']

        # Convert strings to datetime objects
        begin_date_time = datetime.strptime(
            begin_date_time_str, '%m/%d/%Y %H:%M:%S')
        print(f"Begin Date Time: {begin_date_time}")

        end_date_time = datetime.strptime(
            end_date_time_str, '%m/%d/%Y %H:%M:%S')
        print(f"End Date Time: {end_date_time}")

        first_result = data.loc[0, 'Result']
        print(f"First Result: {first_result}")

        # Convert the 'Recipe' string to lowercase and check for "top" or "bot"/"bottom"
        panel_name = data.loc[0, 'Recipe']
        print(f"Panel Name: {panel_name}")
        recipe_path = data.loc[0, 'Recipe'].lower()
        print(f"Recipe Path: {recipe_path}")

        # Determine panel_name based on the presence of "top" or "bot"/"bottom"
        if 'top' in recipe_path:
            panel_type = 'Top'
        elif 'bot' in recipe_path or 'bottom' in recipe_path:
            panel_type = 'Bottom'
        else:
            panel_type = 'Unknown'  # Optional: Handle cases where neither substring is found

        print(f"Panel Type: {panel_type}")
        second_result = None

        # Iterate through the rows of the DataFrame
        # for index, row in data.iterrows():
        #     # Check if the value in the 'Date' column is 'Result'
        #     if row['Date'] == 'Result':
        #         # If found, store the value in the next row of the 'Date' column as second_result
        #         for_result = f"Result:{data.loc[index + 1, 'Date']}"
        #         break
        #     if row['Start Time'] == "Operator Review":
        #         for_operator_review = f"Operator Review:{data.loc[index + 1, 'Date']}"

        #         print(f"Second Result: {second_result}")
        #         break  # Stop iterating once found
        # Initialize the variables
        for_result = None
        for_operator_review = None
        second_result = None

        for index, row in data.iterrows():
            # Check if the value in the 'Date' column is 'Result'
            if row['Date'] == 'Result':
                # If found, store the value in the next row of the 'Date' column as part of a string in for_result
                for_result = f"Result: {data.loc[index + 1, 'Date']}"

            # Check if the value in the 'Start Time' column is 'Operator Review'
            if row['StartTime'] == "Operator Review":
                # If found, store the value in the next row of the 'Date' column as part of a string in for_operator_review
                for_operator_review = f"Operator Review: {data.loc[index + 1, 'StartTime']}"

            # If both for_result and for_operator_review have been assigned, concatenate them and store the result in second_result
            if for_result is not None and for_operator_review is not None:
                second_result = for_result + ","+" " + for_operator_review
                print(f"Second Result: {second_result}")
                break  # Stop iterating once both conditions are met

        # Print the extracted second_result value

        # Add your parsing logic here
        # Process the data and return the result as needed
    except Exception as e:
        print(f"Error occurred while parsing SPI log file: {e}")


if __name__ == "__main__":
    spi_log_file_path = '/home/satvik/Office/SFCS/SFCS-Checklist-Backend/machine_logs/Sample Log Files/SPI/VEPARB34010007_PCBIndex(13857).csv'
    parse_spi_log_file(spi_log_file_path)
