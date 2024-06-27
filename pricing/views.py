from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from datetime import timedelta, datetime
from .models import *
from .serializers import *
from django.utils import timezone
from store_checklist.models import BillOfMaterials, BillOfMaterialsLineItem, Product, Project, Distributor
from store_checklist.serializers import BillOfMaterialsSerializer, BillOfMaterialsLineItemSerializer, ProductSerializer, ProjectSerializer, BillOfMaterialsSerializerNew, BillOfMaterialsLineItemSerializerNew, ManufacturerPartSerializer
from django.db.models import Max
import re
from django_celery_results.models import TaskResult
from django.utils import timezone
import pytz
from .tasks import *
from celery.result import AsyncResult
from django.http import Http404

from .distributors import digikey_online_distributor, Oauth_digikey, mouser_online_distributor, element14_online_distributor , samtec_own_mfg , get_recommended_parts

# @api_view(['GET'])
# def get_product_pricing(request,product_id):
#     purchase_orders = get_purchase_orders_list()
#     # vepl_parts = get_latest_part_numbers(product_id)
#     vepl_parts = ['1962','0383']
#     vepl_part_latest_prices  = []
#     for purchase_order in purchase_orders:
#         if len(vepl_parts)!=0:
#             po_details  = get_purchase_order_details(purchase_order.get('purchaseorder_id'))
#             po_line_items  = po_details.get('line_items')
#             for vepl_part in vepl_parts:
#                 for po_line_item in po_line_items:
#                     # if vepl_part == find_vepl_number(po_line_item.get('name')):
#                     print(vepl_part)
#                     print(po_line_item.get('sku'))
#                     if vepl_part == po_line_item.get('sku'):
#                         print('sku match')
#                         vepl_part_rate = po_line_item.get('rate')
#                         vepl_part_quantity = po_line_item.get('quantity')
#                         vepl_part_total =  po_line_item.get('item_total')
#                         vepl_part_name = po_line_item.get('name')
#                         vepl_part_description = po_line_item.get('description')
#                         vepl_part_latest_prices.append({
#                             'part_number': vepl_part,
#                             'name': vepl_part_name,
#                             'description': vepl_part_description,
#                             'rate': vepl_part_rate,
#                             'quantity': vepl_part_quantity,
#                             'total': vepl_part_total,
#                             'po': po_details
#                         })
#                         if vepl_part in vepl_parts:
#                             vepl_parts.remove(vepl_part)
#         else:
#             break

#     vepl_part_latest_prices.extend([{
#         'part_number': vepl_part,
#         'name': '',
#         'description': '',
#         'rate': '',
#         'quantity': '',
#         'total': ''
#     } for vepl_part in vepl_parts])

#     data = {
#         'part_prices': vepl_part_latest_prices,
#         'latest_parts': vepl_parts
#     }
#     return Response(data,status=status.HTTP_200_OK)


from django.http import JsonResponse
import json

@api_view(['GET'])
def get_project_pricing_page(request):
    try:
        projects = Project.objects.all()
        products = Product.objects.all()
        boms = BillOfMaterials.objects.all()
        projects_serializer = ProjectSerializer(projects, many=True)
        products_serializer = ProductSerializer(products, many=True)
        boms_data = []

        for bom in boms:
            bom_data = BillOfMaterialsSerializerNew(bom).data
            bom_format_name = bom.bom_format.name if bom.bom_format else None
            bom_data['bom_format_name'] = bom_format_name
            boms_data.append(bom_data)

        last_task_result = TaskResult.objects.filter(result='1').order_by('-date_done').first()
        last_updated_at = ''

        if last_task_result:
            utc_time = last_task_result.date_done.replace(tzinfo=pytz.UTC)
            ist_time = utc_time.astimezone(pytz.timezone('Asia/Kolkata'))
            last_updated_at = ist_time.strftime('%d/%m/%Y %I:%M %p')

        data = {
            'projects': projects_serializer.data,
            'products': products_serializer.data,
            'last_updated_at': last_updated_at,
            'boms': boms_data,
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)})



@api_view(['GET'])
def get_bom_pricing(request, bom_id):
    try:
        print("bom id:", bom_id)

        try:
            bom = BillOfMaterials.objects.get(id=bom_id)
        except BillOfMaterials.DoesNotExist:
            raise Http404("Bill of Materials not found for the given bom_id.")

        bom_lineitems = BillOfMaterialsLineItem.objects.filter(bom_id=bom_id)
        line_items_data = []
        final_json = []

        if bom.bom_format and bom.bom_format.name == "Power Electronics":
            for line_item in bom_lineitems:
                first_manufacturer_part = line_item.manufacturer_parts.first()

                if first_manufacturer_part:
                    part_data = ManufacturerPartSerializer(
                        first_manufacturer_part).data

                    distributors = Distributor.objects.all()
                    distributor_responses = {}

                    for distributor in distributors:
                        if distributor.name.lower() == "digikey":
                            distributor_response = digikey_online_distributor(
                                settings.DIGIKEY_APIS_CLIENT_ID,
                                settings.DIGIKEY_APIS_CLIENT_SECRET,
                                first_manufacturer_part.part_number,
                                "DigiKey",
                                bom_id,
                                distributor,
                            )
                            distributor_responses["digikey"] = distributor_response

                        elif distributor.name.lower() == "mouser":
                            distributor_response = mouser_online_distributor(
                                settings.MOUSER_API_KEY,
                                first_manufacturer_part.part_number,
                                "Mouser",
                                bom_id,
                                distributor,
                            )

                        elif distributor.name.lower() == "element14":
                            distributor_response = element14_online_distributor(
                                settings.ELEMENT14_API_KEY,
                                first_manufacturer_part.part_number,
                                # settings.HEADER_IP,                        
                                "Element14",
                                distributor,

                            )
                        elif distributor.name.lower() == 'samtec' and first_manufacturer_part.manufacturer.name.lower() == 'samtec':
                            print("calling Samtec API")
                            distributor_response = samtec_own_mfg(
                                settings.SAMTEC_API_KEY,
                                first_manufacturer_part.part_number,
                                "samtec",
                                distributor,
                            )
                            # distributor_responses["mouser"] = distributor_response
                        # else:
                        #     distributor_responses[distributor.name.lower()] = {'error': f'No API defined for {distributor.name}'}

                        if distributor_response:
                            if distributor_response.get("error"):
                                continue
                            else:
                                distributor_responses[distributor.name] = distributor_response

                    if distributor_response.items():

                        part_data['distributors'] = distributor_responses
                        line_items_data.append(part_data)

                        for distributor_name, distributor_data in distributor_responses.items():
                            row = {
                                "distributor": distributor_name,
                                "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
                                "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
                                "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
                                "Description": distributor_data.get("Description", ""),
                                "Product Url": distributor_data.get("Product Url", ""),
                                "Datasheet Url": distributor_data.get("Datasheet Url", ""),
                                "Package Type": distributor_data.get("Package Type", ""),
                                "Stock": distributor_data.get("Stock", ""),
                                "Currency": distributor_data.get("Currency", "")
                            }

                            # Flatten the pricing information
                            pricing = distributor_data.get("Pricing", [])
                            for price in pricing:
                                row[f"price({price['Quantity']})"] = price["Unit Price"]

                            final_json.append(row)

                    # part_data['distributors'] = distributor_responses
                    # line_items_data.append(part_data)

                    # # Create rows for the final_json
                    # for distributor_name, distributor_data in distributor_responses.items():
                    #     row = {
                    #         "distributor": distributor_name,
                    #         "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
                    #         "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
                    #         "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
                    #         "Description": distributor_data.get("Description", ""),
                    #         "Product Url": distributor_data.get("Product Url", ""),
                    #         "Datasheet Url": distributor_data.get("Datasheet Url", ""),
                    #         "Package Type": distributor_data.get("Package Type", ""),
                    #         "Stock": distributor_data.get("Stock", ""),
                    #         "Currency": distributor_data.get("Currency", "")
                    #     }

                    #     # Flatten the pricing information
                    #     pricing = distributor_data.get("Pricing", [])
                    #     for price in pricing:
                    #         row[f"price({price['Quantity']})"] = price["Unit Price"]

                    #     final_json.append(row)

        else:
            for line_item in bom_lineitems:
                vepl_part_number = line_item.part_number
                manufacturer_parts = line_item.manufacturer_parts.all()

                for manufacturer_part in manufacturer_parts:
                    distributors = Distributor.objects.all()
                    distributor_responses = {}

                    for distributor in distributors:
                        if distributor.name.lower() == "digikey":
                            distributor_response = digikey_online_distributor(
                                settings.DIGIKEY_APIS_CLIENT_ID,
                                settings.DIGIKEY_APIS_CLIENT_SECRET,
                                manufacturer_part.part_number,
                                "DigiKey",
                                bom_id
                            )
                        elif distributor.name.lower() == "mouser":
                            distributor_response = mouser_online_distributor(
                                settings.MOUSER_API_KEY,
                                manufacturer_part.part_number,
                                "Mouser",
                                bom_id 
                            )
                        
                        if distributor.name.lower() == "element14":
                            distributor_response = element14_online_distributor(
                                settings.ELEMENT14_API_KEY,
                                manufacturer_part.part_number, 
                                # settings.HEADER_IP,              
                                "Element14"

                            )
                        # else:
                        #     distributor_responses[distributor.name.lower()] = {'error': f'No API defined for {distributor.name}'}
                        if distributor_response:
                            if distributor_response.get("error"):
                                continue
                            else:
                                distributor_responses[distributor.name.lower(
                                )] = distributor_response

                    if distributor_responses.items():
                        line_item_data = {
                            "VEPL part number": vepl_part_number,
                            "distributors": distributor_responses
                        }
                        line_items_data.append(line_item_data)
                        for distributor_name, distributor_data in distributor_responses.items():
                            row = {
                                "part_number": line_item.part_number,
                                "distributor": distributor_name,
                                "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
                                "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
                                "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
                                "Description": distributor_data.get("Description", ""),
                                "Product Url": distributor_data.get("Product Url", ""),
                                "Datasheet Url": distributor_data.get("Datasheet Url", ""),
                                "Package Type": distributor_data.get("Package Type", ""),
                                "Stock": distributor_data.get("Stock", ""),
                                "Currency": distributor_data.get("Currency", "")
                            }

                            # Flatten the pricing information
                            pricing = distributor_data.get("Pricing", [])
                            for price in pricing:
                                row[f"price({price['Quantity']})"] = price["Unit Price"]

                            final_json.append(row)
        data = {
            'line_items': line_items_data,
            'final_json': final_json
        }

        # print("Response Data", data)
        return JsonResponse(data)

    except BillOfMaterialsLineItem.DoesNotExist:
        raise Http404("Bill of Materials not found for the given bom_id.")
    except Exception as e:
        return JsonResponse({'error': str(e)})


# @api_view(['GET'])
# def get_bom_pricing(request, bom_id):
#     try:
#         print("bom id:", bom_id)

#         try:
#             bom = BillOfMaterials.objects.get(id=bom_id)
#         except BillOfMaterials.DoesNotExist:
#             raise Http404("Bill of Materials not found for the given bom_id.")

#         bom_lineitems = BillOfMaterialsLineItem.objects.filter(bom_id=bom_id)
#         line_items_data = []
#         final_json = []

#         if bom.bom_format and bom.bom_format.name == "Power Electronics":
#             for line_item in bom_lineitems:
#                 first_manufacturer_part = line_item.manufacturer_parts.first()

#                 if first_manufacturer_part:
#                     part_data = ManufacturerPartSerializer(first_manufacturer_part).data

#                     distributors = Distributor.objects.all()
#                     distributor_responses = {}

#                     for distributor in distributors:
#                         if distributor.name.lower() == "digikey":
#                             distributor_response = digikey_online_distributor(
#                                 settings.DIGIKEY_APIS_CLIENT_ID,
#                                 settings.DIGIKEY_APIS_CLIENT_SECRET,
#                                 first_manufacturer_part.part_number,
#                                 "DigiKey",
#                                 bom_id
#                             )
#                             distributor_responses["digikey"] = distributor_response

#                         elif distributor.name.lower() == "mouser":
#                             distributor_response = mouser_online_distributor(
#                                 settings.MOUSER_API_KEY,
#                                 first_manufacturer_part.part_number,
#                                 "Mouser",
#                                 bom_id
#                             )
#                             distributor_responses["mouser"] = distributor_response
#                         else:
#                             distributor_responses[distributor.name.lower()] = {'error': f'No API defined for {distributor.name}'}

#                     part_data['distributors'] = distributor_responses
#                     line_items_data.append(part_data)

#                     # Create rows for the final_json
#                     for distributor_name, distributor_data in distributor_responses.items():
#                         row = {
#                             # "part_number": first_manufacturer_part.part_number,
#                             "distributor": distributor_name,
#                             "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
#                             "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
#                             "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
#                             "Description": distributor_data.get("Description", ""),
#                             "Product Url": distributor_data.get("Product Url", ""),
#                             "Datasheet Url": distributor_data.get("Datasheet Url", ""),
#                             "Package Type": distributor_data.get("Package Type", ""),
#                             "Stock": distributor_data.get("Stock", ""),
#                             "Currency": distributor_data.get("Currency", "")
#                         }

#                         # Flatten the pricing information
#                         pricing = distributor_data.get("Pricing", [])
#                         for price in pricing:
#                             row[f"price({price['Quantity']})"] = price["Unit Price"]

#                         final_json.append(row)
#         else:
#             for line_item in bom_lineitems:
#                 vepl_part_number = line_item.part_number
#                 manufacturer_parts = line_item.manufacturer_parts.all()

#                 for manufacturer_part in manufacturer_parts:
#                     distributor_response = digikey_online_distributor(
#                         settings.DIGIKEY_APIS_CLIENT_ID,
#                         settings.DIGIKEY_APIS_CLIENT_SECRET,
#                         manufacturer_part.part_number,
#                         "DigiKey",
#                         bom_id
#                     )

#                     # Format the distributor response as needed
#                     distributor_data = {
#                         "Manufacturer Part Number": distributor_response.get("Manufacturer Part Number", ""),
#                         "Manufacturer Name": distributor_response.get("Manufacturer Name", ""),
#                         "Online Distributor Name": distributor_response.get("Online Distributor Name", ""),
#                         "Description": distributor_response.get("Description", ""),
#                         "Product Url": distributor_response.get("Product Url", ""),
#                         "Datasheet Url": distributor_response.get("Datasheet Url", ""),
#                         "Package Type": distributor_response.get("Package Type", ""),
#                         "Stock": distributor_response.get("Stock", ""),
#                         "Currency": distributor_response.get("Currency", ""),
#                         "Pricing": distributor_response.get("Pricing", [])
#                     }


#                     line_item_data = {
#                         "VEPL part number": vepl_part_number,
#                         "distributors": {
#                             "digikey": distributor_data
#                         }
#                     }

#                     line_items_data.append(line_item_data)

#                     # Create rows for the final_json
#                     row = {
#                         "part_number": line_item.part_number,
#                         "distributor": "digikey",
#                         "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
#                         "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
#                         "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
#                         "Description": distributor_data.get("Description", ""),
#                         "Product Url": distributor_data.get("Product Url", ""),
#                         "Datasheet Url": distributor_data.get("Datasheet Url", ""),
#                         "Package Type": distributor_data.get("Package Type", ""),
#                         "Stock": distributor_data.get("Stock", ""),
#                         "Currency": distributor_data.get("Currency", "")
#                     }

#                     # Flatten the pricing information
#                     pricing = distributor_data.get("Pricing", [])
#                     for price in pricing:
#                         row[f"price({price['Quantity']})"] = price["Unit Price"]

#                     final_json.append(row)

#         data = {
#             'line_items': line_items_data,
#             'final_json': final_json
#         }

#         # print("Response Data", data)
#         return Response(data, status=status.HTTP_200_OK)

#     except BillOfMaterialsLineItem.DoesNotExist:
#         raise Http404("Bill of Materials not found for the given bom_id.")
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_product_pricing(request, product_id):
    try:
        part_prices = PartPricing.objects.filter(product_id=product_id)
        part_prices_serializer = PartPricingSerializer(part_prices, many=True)

        data = {
            'part_prices': part_prices_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)

    except PartPricing.DoesNotExist:
        raise Http404("Part pricing not found for the given product_id.")

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_project_pricing(request, project_id):
    try:
        part_prices = PartPricing.objects.filter(project_id=project_id)
        part_prices_serializer = PartPricingSerializer(part_prices, many=True)

        data = {
            'part_prices': part_prices_serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)

    except PartPricing.DoesNotExist:
        raise Http404("Part pricing not found for the given product_id.")

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def refresh_product_pricing(request):
    try:
        res = update_pricing_for_all_products.delay()
        task_result = AsyncResult(res.id)
        task_status = task_result.status

        return Response({
            'message': 'Refreshing prices, this might take several minutes.',
            'task_id': res.id,
            'task_status': str(task_status)
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def create_mfr_part_distributor_data(request):
    try:

        # Fetch all ManufacturerPart instances
        manufacturer_parts = ManufacturerPart.objects.all()[:1]
        print(manufacturer_parts)

        # Iterate through each ManufacturerPart
        for manufacturer_part in manufacturer_parts:
            try:
                # Fetch all Distributor instances
                for distributor in Distributor.objects.all():
                    try:
                        # Check distributor type
                        if distributor.name.lower() == "digikey":
                            # distributor_response = digikey_online_distributor(
                            #     settings.DIGIKEY_APIS_CLIENT_ID,
                            #     settings.DIGIKEY_APIS_CLIENT_SECRET,
                            #     manufacturer_part.part_number,
                            #     "DigiKey"
                            # )
                            # Get the Digikey distributor instance
                            digi_key_distributor_instance = Distributor.objects.get(
                                name="Digikey")

                            # Check if access_id and access_secret are available
                            if digi_key_distributor_instance.access_id and digi_key_distributor_instance.access_secret:
                                # Call the API function with the provided credentials
                                distributor_response = digikey_online_distributor(
                                    digi_key_distributor_instance.access_id,
                                    digi_key_distributor_instance.access_secret,
                                    manufacturer_part.part_number,

                                )
                            else:
                                # Handle the case where access_id or access_secret is not available
                                print(
                                    "Access ID or Access Secret not available for Digikey")
                                # You might want to set distributor_response to something indicating the error
                        elif distributor.name.lower() == "mouser":
                            # distributor_response = mouser_online_distributor(
                            #     settings.MOUSER_API_KEY,
                            #     manufacturer_part.part_number,
                            #     "Mouser"
                            # )
                            mouser_distributor_instance = Distributor.objects.get(
                                name="Mouser")
                            if mouser_distributor_instance and mouser_distributor_instance.api_key:
                                # Call the API function with the provided API key
                                distributor_response = mouser_online_distributor(
                                    mouser_distributor_instance.api_key,
                                    manufacturer_part.part_number,
                                )
                                # Check if distributor response is successful
                                if distributor_response and not distributor_response.get("error"):
                                    # Remove dollar sign from prices
                                    pricing = distributor_response.get(
                                        "Pricing", [])
                                    for price in pricing:
                                        if 'Unit Price' in price:
                                            # Remove dollar sign from unit price
                                            unit_price_str = price['Unit Price']
                                            if unit_price_str.startswith('$'):
                                                unit_price_str = unit_price_str[1:]
                                            # Convert price to float and store
                                            try:
                                                unit_price = float(
                                                    unit_price_str)
                                                price['Unit Price'] = unit_price
                                            except ValueError:
                                                print(
                                                    f"Invalid price format: {unit_price_str}")
                                        else:
                                            print(
                                                "No 'Unit Price' key found in pricing")

                            else:
                                # Handle the case where the distributor instance or API key is missing
                                print(
                                    "Distributor instance or API key not available for Mouser")
                                # You might want to set distributor_response to something indicating the error

                        elif distributor.name.lower() == "Element14":
                            element14_distributor_instance = Distributor.objects.get(
                                name="element14")
                            if element14_distributor_instance and element14_distributor_instance.api_key:
                                # Call the API function with the provided API key
                                distributor_response = element14_online_distributor(
                                    element14_distributor_instance.api_key,
                                    manufacturer_part.part_number,
                                )

                            else:
                                print(
                                    "Distributor instance or API key not available for element14")

                            # Print distributor response
                        print(
                            f"Distributor Response for {distributor.name}: {distributor_response}")

                        # If distributor response is successful
                        if distributor_response and not distributor_response.get("error"):

                            currency_name = distributor_response.get(
                                "Currency")
                            print('currency_name in loop', currency_name)
                            currency, _ = Currency.objects.get_or_create(
                                name=currency_name)

                            # Update or create ManufacturerPartDistributorDetail instance
                            mfr_part_distributor_detail, created = ManufacturerPartDistributorDetail.objects.update_or_create(
                                manufacturer_part=manufacturer_part,
                                distributor=distributor,
                                defaults={
                                    'description': distributor_response.get("Description", ""),
                                    'product_url': distributor_response.get("Product Url", ""),
                                    'datasheet_url': distributor_response.get("Datasheet Url", ""),
                                    'stock': distributor_response.get("Stock", ""),
                                    'currency': currency
                                }
                            )

                            # Update or create ManufacturerPartPricing instances
                            pricing = distributor_response.get("Pricing", [])
                            print('pricing in loop', pricing)
                            for price in pricing:
                                ManufacturerPartPricing.objects.update_or_create(
                                    manufacturer_part_distributor_detail=mfr_part_distributor_detail,
                                    quantity=price["Quantity"],
                                    defaults={
                                        'price': price["Unit Price"]}
                                )
                    except Exception as dist_err:
                        print(
                            f"Error processing distributor {distributor.name}: {dist_err}")
            except Exception as part_err:
                print(
                    f"Error processing manufacturer part {manufacturer_part.part_number}: {part_err}")

        return Response({"message": "Manufacturer part distributor data created successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error occurred: {e}")
        return Response({"error": "An error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.http import JsonResponse

@api_view(["GET"])
def get_manufacture_part_pricing(request, bom_id):
   
    bom_line_items = BillOfMaterialsLineItem.objects.filter(bom_id=bom_id)

    # Collect the manufacturer part ids and part numbers (VEPL Numbers)
    manufacturer_parts = {}
    for item in bom_line_items:
        for part in item.manufacturer_parts.all():
            manufacturer_parts[part.id] = item.part_number

    # Filter ManufacturerPartDistributorDetail based on the extracted manufacturer part ids
    manufacturer_pricing = ManufacturerPartDistributorDetail.objects.filter(
        manufacturer_part_id__in=manufacturer_parts.keys()
    )

    # Serialize the filtered manufacturer parts
    serializers = ManufacturerPartDistributorDetailSerializer(manufacturer_pricing, many=True)
    data = serializers.data
    final_data = []

    for item in data:
        manufacturer_part_id = item['manufacturer_part']['id']
        vepl_number = manufacturer_parts.get(manufacturer_part_id, "Unknown")
        print(f"Mapping manufacturer_part_id {manufacturer_part_id} to VEPL Number: {vepl_number}")  

        # Initialize the row dictionary with the required fields
        row = {
            'VEPL Number': vepl_number,  # Map VEPL Number using part number
            'Manufacturer Part Number': item['manufacturer_part']['part_number'],
            'Online Distributor Name': item['distributor']['name'],
            'Manufacturer': item['manufacturer_part']['manufacturer']['name'],
            'Description': item.get('description'),
            'Stock': item.get('stock'),
            'Currency': item['currency']['name'],
            'Symbol' : item['currency']['symbol'],
            'Datasheet Url': item.get('datasheet_url'),
            'Product Url': item.get('product_url')
        }

        # Fetch pricing details for the current ManufacturerPartDistributorDetail
        manufacturer_part_distributor_detail_id = item['id']
        pricing_details = ManufacturerPartPricing.objects.filter(
            manufacturer_part_distributor_detail=manufacturer_part_distributor_detail_id
        )
        pricing_serializer = ManufacturerPartPricingSerializer(pricing_details, many=True)
        
        # Add pricing details dynamically
        for pricing_detail in pricing_serializer.data:
            quantity = pricing_detail['quantity']
            price_field = f'Price ({quantity})'
            row[price_field] = pricing_detail['price']

        final_data.append(row)

    return JsonResponse(final_data, safe=False)



# @api_view(['GET'])
# def get_pricing_details(request):
#     try:
#         part_number = request.query_params.get("part_number")

#         if not part_number:
#             return JsonResponse({'error': 'Part number is required'}, status=400)

#         distributors = Distributor.objects.all()
#         distributor_responses = {}
#         line_items_data = []
#         final_json = []
#         part_data = {}

#         for distributor in distributors:
#             distributor_response = None
#             if distributor.name.lower() == "digikey":
#                 distributor_response = digikey_online_distributor(
#                     settings.DIGIKEY_APIS_CLIENT_ID,
#                     settings.DIGIKEY_APIS_CLIENT_SECRET,
#                     part_number,
#                 )
#             elif distributor.name.lower() == "mouser":
#                 distributor_response = mouser_online_distributor(
#                     settings.MOUSER_API_KEY,
#                     part_number,
#                 )
#             elif distributor.name.lower() == "element14":
#                 distributor_response = element14_online_distributor(
#                     settings.ELEMENT14_API_KEY,
#                     part_number,
#                 )

#             if distributor_response:
#                 if distributor_response.get("error"):
#                     continue
#                 else:
#                     distributor_responses[distributor.name.lower()] = distributor_response

#         if distributor_responses:
#             part_data['distributors'] = distributor_responses
#             line_items_data.append(part_data)

#             for distributor_name, distributor_data in distributor_responses.items():
#                 currency_name = distributor_data.get("Currency", "")
#                 try:
#                     currency = Currency.objects.get(name=currency_name)
#                     currency_symbol = currency.symbol
#                 except Currency.DoesNotExist:
#                     currency_symbol = ""

#                 row = {
#                     "distributor": distributor_name,
#                     "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
#                     "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
#                     "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
#                     "Description": distributor_data.get("Description", ""),
#                     "Product Url": distributor_data.get("Product Url", ""),
#                     "Datasheet Url": distributor_data.get("Datasheet Url", ""),
#                     "Package Type": distributor_data.get("Package Type", ""),
#                     "Stock": distributor_data.get("Stock", ""),
#                     "Currency": distributor_data.get("Currency", ""),
#                     "Currency Symbol": currency_symbol,
#                 }

#                 pricing = distributor_data.get("Pricing", [])
#                 for price in pricing:
#                     row[f"price({price['Quantity']})"] = price["Unit Price"]

#                 final_json.append(row)

#         data = {
#             'line_items': line_items_data,
#             'final_json': final_json
#         }

#         return JsonResponse(data)

#     except BillOfMaterialsLineItem.DoesNotExist:
#         raise Http404("Bill of Materials not found for the given bom_id.")
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
def get_pricing_details(request):
    try:
        part_number = request.query_params.get("part_number")

        if not part_number:
            return JsonResponse({'error': 'Part number is required'}, status=400)

        distributors = Distributor.objects.all()
        print("Distributors fetched:", distributors)
        
        distributor_responses = {}
        line_items_data = []
        final_json = []
        part_data = {}

        for distributor in distributors:
            distributor_response = None
            print(f"Processing distributor: {distributor.name}")

            if distributor.name.lower() == "digikey":
                print("Calling Digikey API")
                distributor_response = digikey_online_distributor(
                    # settings.DIGIKEY_APIS_CLIENT_ID,
                    # settings.DIGIKEY_APIS_CLIENT_SECRET,
                    distributor.access_id,
                    distributor.access_secret,
                    part_number,
                    distributor,
                )
            elif distributor.name.lower() == "mouser":
                print("Calling Mouser API")
                distributor_response = mouser_online_distributor(
                    # settings.MOUSER_API_KEY,
                    distributor.api_key,
                    part_number,
                    distributor
                  
                )
            elif distributor.name.lower() == "element14":
                print("Calling Element14 API")
                distributor_response = element14_online_distributor(
                    # settings.ELEMENT14_API_KEY,
                    distributor.api_key,
                    part_number,
                    distributor,
                    
                )
            
            elif distributor.name.lower() == 'samtec':

                print("calling Samtec API")
                distributor_response = samtec_own_mfg(
                #    settings.SAMTEC_API_KEY,
                   distributor.api_key,
                   part_number,
                   "samtec" ,
                   distributor,
                )

            print(f"Response from {distributor.name} API:", distributor_response)

            if distributor_response:
                if distributor_response.get("error"):
                    print(f"Error in {distributor.name} response:", distributor_response.get("error"))
                    continue
                else:
                    distributor_responses[distributor.name] = distributor_response

        if distributor_responses:
            part_data['distributors'] = distributor_responses
            line_items_data.append(part_data)

            for distributor_name, distributor_data in distributor_responses.items():
                currency_name = distributor_data.get("Currency", "")
                try:
                    currency = Currency.objects.get(name=currency_name)
                    currency_symbol = currency.symbol
                except Currency.DoesNotExist:
                    currency_symbol = ""

                row = {
                    "distributor": distributor_name,
                    "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
                    "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
                    "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
                    "Description": distributor_data.get("Description", ""),
                    "Product Url": distributor_data.get("Product Url", ""),
                    "Datasheet Url": distributor_data.get("Datasheet Url", ""),
                    "Package Type": distributor_data.get("Package Type", ""),
                    "Stock": distributor_data.get("Stock", ""),
                    "Currency": distributor_data.get("Currency", ""),
                    "Currency Symbol": currency_symbol,
                }

                pricing = distributor_data.get("Pricing", [])
                for price in pricing:
                    quantity = price["Quantity"]
                    unit_price = price["Unit Price"]

                    # Convert price to numeric format
                    if isinstance(unit_price, str):
                        try:
                            unit_price = float(unit_price.replace("$", "").replace(",", ""))
                        except ValueError:
                            unit_price = None

                    row[f"price({quantity})"] = unit_price

                final_json.append(row)

        data = {
            'line_items': line_items_data,
            'final_json': final_json
        }

        return JsonResponse(data)

    except BillOfMaterialsLineItem.DoesNotExist:
        raise Http404("Bill of Materials not found for the given bom_id.")
    except Exception as e:
        print("An error occurred:", str(e))
        return JsonResponse({'error': str(e)}, status=500)

        
@api_view(['GET'])
def get_VeplNumber_prices(request):
    try:
        vepl_number = request.query_params.get("part_number")

        if not vepl_number:
            return JsonResponse({'error': 'VEPL number is required'}, status=400)

        # Fetch the BillOfMaterialsLineItems using the VEPL number
        line_items = BillOfMaterialsLineItem.objects.filter(part_number=vepl_number)

        if not line_items.exists():
            return JsonResponse({'error': 'VEPL number not found'}, status=404)

        final_json = []
        line_items_data = []

        # Iterate over the line items and fetch related manufacturer parts
        for line_item in line_items:
            manufacturer_parts = line_item.manufacturer_parts.all()

            if not manufacturer_parts:
                continue

            for part in manufacturer_parts:
                distributors = Distributor.objects.all()
                distributor_responses = {}
                part_data = {}

                for distributor in distributors:
                    distributor_response = None
                    if distributor.name.lower() == "digikey":
                        distributor_response = digikey_online_distributor(
                            # settings.DIGIKEY_APIS_CLIENT_ID,
                            # settings.DIGIKEY_APIS_CLIENT_SECRET,
                            distributor.access_id,
                            distributor.access_secret,
                            part.part_number,
                            distributor,
                        )
                    elif distributor.name.lower() == "mouser":
                        distributor_response = mouser_online_distributor(
                            # settings.MOUSER_API_KEY,
                            distributor.api_key,
                            part.part_number,
                            distributor,
                        )
                    elif distributor.name.lower() == "element14":
                        distributor_response = element14_online_distributor(
                            # settings.ELEMENT14_API_KEY,
                            distributor.api_key,
                            part.part_number,
                            distributor,
                        )
                    elif distributor.name.lower() == 'samtec' and part.manufacturer.name.lower() == 'samtec':
                        print("calling Samtec API")
                        distributor_response = samtec_own_mfg(
                            # settings.SAMTEC_API_KEY,
                            distributor.api_key,
                            part.part_number,
                            "samtec",
                            distributor,
                        )

                    if distributor_response:
                        if distributor_response.get("error"):
                            continue
                        else:
                            distributor_responses[distributor.name] = distributor_response

                if distributor_responses:
                    part_data['distributors'] = distributor_responses
                    line_items_data.append(part_data)

                    for distributor_name, distributor_data in distributor_responses.items():
                        currency_name = distributor_data.get("Currency", "")
                        try:
                            currency = Currency.objects.get(name=currency_name)
                            currency_symbol = currency.symbol
                        except Currency.DoesNotExist:
                            currency_symbol = ""

                        row = {
                            "vepl_number": vepl_number,
                            "distributor": distributor_name,
                            "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
                            "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
                            "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
                            "Description": distributor_data.get("Description", ""),
                            "Product Url": distributor_data.get("Product Url", ""),
                            "Datasheet Url": distributor_data.get("Datasheet Url", ""),
                            "Package Type": distributor_data.get("Package Type", ""),
                            "Stock": distributor_data.get("Stock", ""),
                            "Currency": distributor_data.get("Currency", ""),
                            "Currency Symbol": currency_symbol,
                        }

                        pricing = distributor_data.get("Pricing", [])
                        for price in pricing:
                            unit_price = price["Unit Price"]
                            if isinstance(unit_price, str):
                                unit_price = float(unit_price.replace('$', '').replace(',', '').strip())
                            row[f"price({price['Quantity']})"] = unit_price

                        final_json.append(row)

        data = {
            'vepl_number': vepl_number,
            'line_items': line_items_data,
            'final_json': final_json
        }

        return JsonResponse(data)

    except BillOfMaterialsLineItem.DoesNotExist:
        raise Http404("Bill of Materials not found for the given VEPL number.")
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


api_view(["GET"])
def get_recommendation_details(request):
    description = request.GET.get('description')

    if not description:
        return JsonResponse({'error': 'Description is Required'}, status=400)

    recommendations = get_recommended_parts(description, settings.DIGIKEY_APIS_CLIENT_ID)

    final_json = []
    line_items_data = []

    for part_data in recommendations['Recommendations']:
        distributor_responses = {part_data["Online Distributor Name"]: part_data.copy()}  # Use .copy() to avoid modifying original part_data
        part_data['distributors'] = distributor_responses
        line_items_data.append(part_data)

        for distributor_name, distributor_data in distributor_responses.items():
            currency_name = distributor_data.get("Currency", "")
            try:
                currency = Currency.objects.get(name=currency_name)
                currency_symbol = currency.symbol
            except Currency.DoesNotExist:
                currency_symbol = ""

            row = {
                "distributor": distributor_name,
                "Manufacturer Part Number": distributor_data.get("Manufacturer Part Number", ""),
                "Manufacturer Name": distributor_data.get("Manufacturer Name", ""),
                "Online Distributor Name": distributor_data.get("Online Distributor Name", ""),
                "Description": distributor_data.get("Description", ""),
                "Product Url": distributor_data.get("Product Url", ""),
                "Datasheet Url": distributor_data.get("Datasheet Url", ""),
                "Package Type": distributor_data.get("Package Type", ""),
                "Stock": distributor_data.get("Stock", ""),
                "Currency": distributor_data.get("Currency", ""),
                "Currency Symbol": currency_symbol,
            }

            pricing = distributor_data.get("Pricing", [])
            for price in pricing:
                quantity = price["Quantity"]
                unit_price = price["Unit Price"]

                # Convert price to numeric format
                if isinstance(unit_price, str):
                    try:
                        unit_price = float(unit_price.replace("$", "").replace(",", ""))
                    except ValueError:
                        unit_price = None

                row[f"price({quantity})"] = unit_price

            final_json.append(row)

    data = {
        'line_items': line_items_data,
        'final_json': final_json
    }

    return JsonResponse(data)


    





