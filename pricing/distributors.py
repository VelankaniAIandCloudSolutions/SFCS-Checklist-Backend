from fastapi import FastAPI
import json
from django.http import Http404
import requests
import pandas as pd

from django.utils import timezone
from datetime import timedelta
from .models import *
from django.conf import settings

from store_checklist.models import BillOfMaterials


def dataExtraction_BOM_file(bom_filename):
    # reading the .bom file and extracting the Mfg part number , mfg description, mfg name
    with open(bom_filename, 'r') as file:
        lines = file.readlines()[12:]  # skip first 12 unwanted rows
        bom_list = []
        for i in lines:
            ls = i.split('\t')
            bom_list.append(ls)
        mfg_pn_list = []
        descrip_list = []
        mfg_name_list = []
        for part_list in bom_list:
            mfg_descrip = part_list[6] if len(part_list) > 6 else None
            if mfg_descrip == None:
                continue
            descrip_list.append(mfg_descrip)
            mfg_name = part_list[7] if len(part_list) > 7 else None
            if mfg_name == None:
                continue
            mfg_name_list.append(mfg_name)
            mfg_pn = part_list[8] if len(part_list) > 8 else None
            if mfg_pn == None:
                continue
            mfg_pn_list.append(mfg_pn)
        # print("\n the mfg part no:==============================\n",mfg_pn_list)
        # print("\n the mfg name:==============================\n",mfg_name_list)
        # print("\n the mfg description :==============================\n",descrip_list)

        # Sample part numbers
        """pn_list = [
            '860020672011', 'CL21A475KBQNNNE', 'C1206C102KBRAC7800', '860020373011', 'TMK316B7225KL-T',
            'CC0805KRX7R9BB223', 'CC0603KRX7R9BB331', 'CL21B105KBFNNNE', 'CGA5L4X7T2W104K160AA',
            'DFLR1200-7', 'BAV21WS-7-F', 'MMSZ4694-TP', 'NA', 'PH1RB-06-UA', 'PH1RB-02-UA',
            'NVMFS005N10MCLT1G', 'RMCF1206FT2M00', 'RC1206FR-071M54L', 'ERJ-8GEYJ680V', 'ERJ-8ENF1003V',
            'RK73B2ATTD103J', 'RC1206JR-073K3L', 'RC1206JR-0747RL', 'ERJ-8ENF20R0V', 'RMCF1206JT1K00',
            'ERJ-6ENF1003V', 'ERJ-6ENF1182V', 'RC0805FR-071KL', 'ERJ-6GEYJ391V', 'INN3167C-H101-TL'
        ]"""

        # entire data
        pn_list = ['CHV1206N1K0471JCT', '860020672011', 'CL21A475KBQNNNE', 'C1206C102KBRAC7800', '860020373011', 'TMK316B7225KL-T', 'CC0805KRX7R9BB223', 'CC0603KRX7R9BB331', 'CL21B105KBFNNNE', 'CGA5L4X7T2W104K160AA', 'S1M', 'DFLR1200-7', 'BAV21WS-7-F', 'MMSZ4694-TP', 'NA', 'PH1RB-06-UA', 'PH1RB-02-UA',
                   'NVMFS005N10MCLT1G', 'RMCF1206FT2M00', 'RC1206FR-071M54L', 'ERJ-8GEYJ680V', 'ERJ-8ENF1003V', 'RK73B2ATTD103J', 'RC1206JR-073K3L', 'RC1206JR-0747RL', 'ERJ-8ENF20R0V', 'RMCF1206JT1K00', 'ERJ-6ENF1003V', 'ERJ-6ENF1182V', 'RC0805FR-071KL', 'ERJ-6GEYJ391V', 'Custom_Flyback_Transformer', 'INN3167C-H101-TL']

        return mfg_pn_list, mfg_name_list


def Oauth_digikey():
    url = "https://api.digikey.com/v1/oauth2/token"
    payload = {
        'client_id': settings.DIGIKEY_APIS_CLIENT_ID,
        'client_secret': settings.DIGIKEY_APIS_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        token_info = response.json()
        access_token = token_info["access_token"]
        expires_in = token_info["expires_in"]
        expiry_date_time = timezone.now() + timedelta(seconds=expires_in)

        AccessToken.objects.create(
            access_token=access_token,
            expires_in=expires_in,
            expiry_date_time=expiry_date_time,
            token_type='digikey'
        )
        return access_token
    except requests.RequestException as e:
        # Log the error and return None or raise an exception
        print("Error obtaining access token:", e)
        return None


def get_digikey_access_token():
    current_access_token = AccessToken.objects.filter(
        token_type='digikey').first()

    if current_access_token is None or current_access_token.expiry_date_time < timezone.now():

        if current_access_token:
            current_access_token.delete()
        access_token = Oauth_digikey()
    else:
        access_token = current_access_token.access_token

    return access_token


# def digikey_online_distributor(client_id, client_secret, part_number, web_name, bom_id):
def digikey_online_distributor(client_id, client_secret, part_number,):
    access_token = get_digikey_access_token()
    if not access_token:
        return {"Manufacturer Part Number": part_number, "error": "Failed to obtain access token"}

    print("token:--->", access_token, "\n")

    # try:
    #     bom = BillOfMaterials.objects.get(id=bom_id)
    # except BillOfMaterials.DoesNotExist:
    #     raise Http404("Bill of Materials not found for the given bom_id.")

    try:
        distributor = Distributor.objects.get(name="Digikey")
        base_url = distributor.api_url
        url = f"{base_url}{part_number}/productdetails"
        print('digi_key url from db', url)
        # url = f"https://api.digikey.com/products/v4/search/{part_number}/productdetails"

        headers = {
            'X-DIGIKEY-Client-Id': client_id,
            'Authorization': f'Bearer {access_token}',
            'X-DIGIKEY-Locale-Site': 'US',
            'X-DIGIKEY-Locale-Language': 'en',
            'X-DIGIKEY-Locale-Currency': 'USD',
            'X-DIGIKEY-Customer-Id': '0'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        digikey_api_response = response.json()

        # print(
        #     f"bom_id: {bom_id}, digikey_api_response: {digikey_api_response}")
        # print(
        #     f"mfr_part: {part_number}, digikey_api_response: {digikey_api_response}")

        product = digikey_api_response.get("Product", {})
        mfg_part_number = product.get("ManufacturerProductNumber")
        mfg_name = product.get("Manufacturer", {}).get("Name")
        description = product.get("Description", {}).get("DetailedDescription")
        currency = digikey_api_response.get(
            "SearchLocaleUsed", {}).get("Currency", "USD")
        product_url = product.get("ProductUrl")
        datasheet_url = product.get("DatasheetUrl")
        package_type = 'N/A'
        standard_pricing = []
        found_data = False
        for variation in product.get("ProductVariations", []):
            package_id = variation.get("PackageType", {}).get("Id")
            # if bom.bom_format and bom.bom_format.name == "Power Electronics":
            package_type_details = DistributorPackageTypeDetail.objects.filter(
                distributor=distributor)

            # Iterate through each related DistributorPackageTypeDetail instance
            for package_type_detail in package_type_details:
                # package_id = package_type_detail.package_type_id
                # Use the package type IDs dynamically from the related fields
                if package_id in [package_type_detail.related_field]:
                    package_type = package_type_detail.package_type.name
                    standard_pricing = variation.get("StandardPricing", [])
                    found_data = True
                    break

        if not found_data:
            for variation in product.get("ProductVariations", []):
                package_type = variation.get(
                    "PackageType", {}).get("Name", "N/A")
                standard_pricing = variation.get("StandardPricing", [])
                break

            # else:
            #     package_type = variation.get("PackageType", {}).get("Name", "N/A")
            #     standard_pricing = variation.get("StandardPricing", [])
            #     break
            # elif package_id:  # Not Power Electronics and has a package ID
            #     package_type = variation.get("PackageType", {}).get("Name", "N/A")
            #     standard_pricing = variation.get("StandardPricing", [])
            #     break

        in_stock = product.get("QuantityAvailable", 0)
        standard_pricing_data = [
            {"Quantity": price["BreakQuantity"],
                "Unit Price": price["UnitPrice"]}
            for price in standard_pricing
        ]

        print("standard_pricing_data:", standard_pricing_data)
        standard_json = {
            "Manufacturer Part Number": mfg_part_number,
            "Manufacturer Name": mfg_name,
            # "Online Distributor Name": web_name,
            "Online Distributor Name": distributor.name,
            "Description": description,
            "Product Url": product_url,
            "Datasheet Url": datasheet_url,
            "Package Type": package_type,
            "Stock": in_stock,
            "Currency": currency,
            "Pricing": standard_pricing_data
        }

        # print(f"bom_id: {bom_id}, Response data: {standard_json}")
        print(f"mfr_part: {part_number}, Response data: {standard_json}")
        return standard_json

    except requests.RequestException as e:
        return {"Manufacturer Part Number": part_number, "error": str(e)}


# def mouser_online_distributor(key, part_number, web_name, bom_id):
def mouser_online_distributor(key, part_number):
    print(f"Mouser ----- {part_number}")
    # calling mouser api
    distributor = Distributor.objects.get(name="mouser")
    key = distributor.api_key

    # key = "daf53999-5620-4003-8217-5c2ed9947d13"
    try:
        base_url = distributor.api_url
        url = f"{base_url}{key}"
        print('mouser url from db', url)
        # url = f"https://api.mouser.com/api/v1/search/keyword?apiKey={key}"
        payload = json.dumps({
            "SearchByKeywordRequest": {
                "keyword": part_number,
                "records": 0,
                "startingRecord": 0,
                "searchOptions": "string",
                "searchWithYourSignUpLanguage": "string"
            }
        })
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        API_response = response.json()

        # transform mouser api response into standard Vepl format
        no_of_results = API_response["SearchResults"]["NumberOfResult"]
        # condition to fetch the exact part number as per the Part.no in BOM file

        mouser_package_types = DistributorPackageTypeDetail.objects.filter(
            distributor__name="mouser"
        ).values_list('related_field', flat=True)
        for index in range(no_of_results):
            part = API_response["SearchResults"]["Parts"][index]
            if part["ManufacturerPartNumber"] == part_number:
                PackageType = "N/A"
                for attribute in part["ProductAttributes"]:
                    # if attribute["AttributeName"] == "Packaging" and attribute["AttributeValue"] in ["Cut Tape", "Ammo Pack", "Bulk"]:
                    if attribute["AttributeName"] == "Packaging" and attribute["AttributeValue"] in mouser_package_types:
                        PackageType = attribute["AttributeValue"]
                        break
                Standard_Pricing = [{
                    "Quantity": price["Quantity"],
                    "Unit Price": price["Price"]
                } for price in part["PriceBreaks"]]

                std_data = {
                    "Manufacturer Part Number": part["ManufacturerPartNumber"],
                    "Manufacturer Name": part["Manufacturer"],
                    # "Online Distributor Name": web_name,
                    "Online Distributor Name": distributor.name,
                    "Description": part["Description"],
                    "Product Url": part["ProductDetailUrl"],
                    "Datasheet Url": part["DataSheetUrl"],
                    "Package Type": PackageType,
                    "Stock": part["AvailabilityInStock"],
                    "Currency": part["PriceBreaks"][0]["Currency"] if part["PriceBreaks"] else "USD",
                    "Pricing": Standard_Pricing
                }
                return std_data
        return {"Manufacturer Part Number": part_number, "Online Distributor Name": str(distributor.name), "error": "Part number not found", "API_response": API_response}
    except Exception as e:
        return {"Manufacturer Part Number": part_number, "Online Distributor Name": str(distributor.name), "error": str(e)}


def element14_online_distributor(key, part_number):
    print(f"Element14 ----------- {part_number}")

    try:
        # key = "574e2u973fa67jt6wb5et68z"
        element14_distributor_instance = Distributor.objects.get(
            name="element14")
        key = element14_distributor_instance.api_key
        base_url = element14_distributor_instance.api_url
        # calling API
        # url = f"https://api.element14.com/catalog/products?versionNumber=1.3&term=manuPartNum%3A{part_number}&storeInfo.id=www.newark.com&resultsSettings.offset=0&resultsSettings.numberOfResults=1&resultsSettings.refinements.filters=rohsCompliant%2CinStock&resultsSettings.responseGroup=large&callInfo.omitXmlSchema=false&callInfo.responseDataFormat=json&callinfo.apiKey={key}"        url = f"https://api.element14.com/catalog/products?versionNumber=1.3&term=manuPartNum%3A{part_number}&storeInfo.id=www.newark.com&resultsSettings.offset=0&resultsSettings.numberOfResults=1&resultsSettings.refinements.filters=rohsCompliant%2CinStock&resultsSettings.responseGroup=large&callInfo.omitXmlSchema=false&callInfo.responseDataFormat=json&callinfo.apiKey={key}"
        # headers = {'X-Originating-IP': header_ip}

        # Construct the URL with query parameters
        query_params = {
            "versionNumber": "1.3",
            "term": f"manuPartNum:{part_number}",
            "storeInfo.id": "www.newark.com",
            "resultsSettings.offset": "0",
            "resultsSettings.numberOfResults": "1",
            "resultsSettings.refinements.filters": "rohsCompliant,inStock",
            "resultsSettings.responseGroup": "large",
            "callInfo.omitXmlSchema": "false",
            "callInfo.responseDataFormat": "json",
            "callinfo.apiKey": key
        }
        url = f"{base_url}?{requests.compat.urlencode(query_params)}"
        response = requests.get(url)
        api_response = response.json()

        # Transform API response into standard format
        no_of_results = api_response["manufacturerPartNumberSearchReturn"]["numberOfResults"]
        # filtering the 0-results Parts
        if no_of_results == 0:
            return {"Manufacturer Part Number": part_number, "Online Distributor Name": str(element14_distributor_instance.name), "Error": "Part Number Not found (or) Stock = 0", "Api_response": api_response}

        element14_package_types = DistributorPackageTypeDetail.objects.filter(
            distributor__name="element14"
        ).values_list('related_field', flat=True)
        for index in range(no_of_results):
            part = api_response["manufacturerPartNumberSearchReturn"]["products"][index]
            if part_number in part["translatedManufacturerPartNumber"] or part_number.replace("-", "") in part["translatedManufacturerPartNumber"]:
                # if part["packageName"] in ["Cut Tape", "Each"]:
                if part["packageName"] in element14_package_types:
                    Standard_Pricing = [
                        {"Quantity": i["from"], "Unit Price": i["cost"]} for i in part["prices"]]
                    std_data = {
                        "Manufacturer Part Number": part["translatedManufacturerPartNumber"],
                        "Online Distributor Name": element14_distributor_instance.name,
                        "Manufacturer Name": part["vendorName"],
                        "Description": part["displayName"],
                        "Product Url": part["productURL"],
                        "Datasheet Url": part["datasheets"][0]["url"] if "datasheets" in part else "N/A",
                        "Package Type": part["packageName"],
                        "Stock": part["stock"]["level"],
                        "Currency": "USD",
                        "Pricing": Standard_Pricing
                    }
                    return std_data
        return {"Manufacturer Part Number": part_number, "Online Distributor Name": str(element14_distributor_instance.name), "error": "Part number not found", "API_response": api_response}
    except Exception as e:
        return {"Manufacturer Part Number": part_number, "Online Distributor Name": str(element14_distributor_instance.name), "error": str(e)}


def api_call(distributor_name, part_no):
    # important credentials are specified inside this function.
    if distributor_name == "digikey":
        client_id = "8mG60KW8HvJYHk2hCiLDGANQ9HossidT"
        client_secret = "euhdJWXXdnd6rH4s"
        return digikey_online_distributor(client_id, client_secret, part_no, distributor_name)

    if distributor_name == "mouser":
        mouser_apikey = " "
        return mouser_online_distributor(mouser_apikey, part_no, distributor_name)

    if distributor_name == "element14":
        element14_apikey = " "
        request_header_ip = " "
        return element14_online_distributor(element14_apikey, request_header_ip, distributor_name)


def convert_stdjson_to_excel(frontend_vepl_json):
    # creating whole list consists of all distributors
    ls = []
    for i in frontend_vepl_json:
        digi_data = i["online_distributors"]["digikey"]
        # checks if the data is present
        if digi_data:
            ls.append(digi_data)
        mou_data = i["online_distributors"]["mouser"]
        if mou_data:
            ls.append(mou_data)
        ele_data = i["online_distributors"]["element14"]
        if ele_data:
            ls.append(ele_data)

    # columns to be displayed in excel
    col_names = ["Mfg_part_number", "online_distributor", "Mfg_name", "Description", "Package_type", "Stock",
                 "Currency", "Price/1-Qty", "Price/50-Qty", "Price/100-Qty", "Price/500-Qty", "Price/1000-Qty", "Price/10000-Qty"]

    # Create an empty DataFrame with the specified columns
    df = pd.DataFrame(columns=col_names)

    for product in ls:
        # Initialize price columns
        price_1_qty = price_50_qty = price_100_qty = price_500_qty = price_1000_qty = price_10000_qty = None

        # Extract pricing information based on quantity
        for price in product.get("Pricing", []):
            if price["Quantity"] == 1:
                price_1_qty = price["Unit Price"]
            elif price["Quantity"] == 50:
                price_50_qty = price["Unit Price"]
            elif price["Quantity"] == 100:
                price_100_qty = price["Unit Price"]
            elif price["Quantity"] == 500:
                price_500_qty = price["Unit Price"]
            elif price["Quantity"] == 1000:
                price_1000_qty = price["Unit Price"]
            elif price["Quantity"] == 10000:
                price_10000_qty = price["Unit Price"]

        # Add the product details to the DataFrame
        df.loc[len(df)] = [
            product.get("Manufacturer Part Number", "N/A"),
            product.get("Online Distributor Name", "N/A"),
            product.get("Manufacturer Name", "N/A"),
            product.get("Description", "N/A"),
            product.get("Package Type", "N/A"),
            product.get("Stock", "N/A"),
            product.get("Currency", "N/A"),
            price_1_qty,
            price_50_qty,
            price_100_qty,
            price_500_qty,
            price_1000_qty,
            price_10000_qty
        ]

    return df


###################################### MAIN PROGRAM ######################################
# if __name__ == "__main__":

app = FastAPI()


@app.get("/")
async def root(part_numbers, manufacturer_names, client_id, client_secret):

    # BOM file name
    # bom_file_name = "gen2_1600w_aux_supply.BOM"
    # calling data extraction function
    # part_numbers, manufacturer_names = dataExtraction_BOM_file(bom_file_name)

    # sample for code
    # part_numbers = ['CHV1206N1K0471JCT', '860020672011', 'CL21A475KBQNNNE']
    # manufacturer_names = ['Cal-Chip Electronics, Inc.', 'Würth Elektronik', 'Samsung Electro-Mechanics']
    print("\n partnumbers: -------------\n\n", part_numbers, "\n\n",
          "\n manufacturer name: -------------\n\n", manufacturer_names, "\n ")

    # Initialize an empty list to store JSON objects
    frontend_json = []

    # Use the zip function to iterate over both lists simultaneously
    for pn, mfg in zip(part_numbers, manufacturer_names):
        print(pn, mfg)
        part_info = {
            "Part_Number": pn,
            "Manufacturer_Name": mfg,
            "online_distributors": {
                # calling API functions
                "digikey": api_call("digikey", pn, client_id, client_secret),
                "mouser": api_call("mouser", pn),
                "element14": api_call("element14", pn),
            }
        }
        frontend_json.append(part_info)

    # Print the final JSON-like structure
    # print(json.dumps(frontend_json, indent=4))
    vepl_json_format = json.dumps(frontend_json, indent=4)
    # writing the output in json files
    with open("generic_vepl_json.json", 'w') as f:
        f.write(vepl_json_format)

    # call function for converting json into excel
    data_frame = convert_stdjson_to_excel(frontend_json)
    data_frame.to_excel("generic_veplexcel.xlsx")
    # print(data_frame)
    return vepl_json_format


# if package_id in [2, 3, 62]:
#     package_type = variation.get(
#         "PackageType", {}).get("Name", "N/A")
#     standard_pricing = variation.get("StandardPricing", [])
#     found_data = True
