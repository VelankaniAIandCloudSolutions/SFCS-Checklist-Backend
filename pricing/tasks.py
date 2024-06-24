from celery import shared_task
from fastapi import Response
from store_checklist.models import Product
from .models import PartPricing
import requests
from django.conf import settings
from datetime import timedelta
from .models import *
from django.utils import timezone
from store_checklist.models import BillOfMaterials, BillOfMaterialsLineItem, Product, Project
from django.db.models import Max
import re
import logging
from django.conf import settings

from .distributors import digikey_online_distributor, Oauth_digikey, mouser_online_distributor, element14_online_distributor
logger = logging.getLogger(__name__)


def refresh_access_token(refresh_token, client_id, client_secret, redirect_uri):
    url = "https://accounts.zoho.in/oauth/v2/token"

    params = {
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, params=params)
    AccessToken.objects.create(access_token=response.json().get('access_token'), expires_in=response.json().get(
        'expires_in'), expiry_date_time=timezone.now() + timedelta(seconds=response.json().get('expires_in')))
    return response.json()


def get_access_token():

    current_access_token = AccessToken.objects.first()
    token_expired = False
    if current_access_token is None:
        response = refresh_access_token(settings.ZOHO_APIS_REFRESH_TOKEN, settings.ZOHO_APIS_CLIENT_ID,
                                        settings.ZOHO_APIS_CLIENT_SECRET, settings.ZOHO_APIS_REDIRECT_URI)
        token_expired = True
        access_token = response.get('access_token')
    else:
        if current_access_token.expiry_date_time < timezone.now():
            current_access_token.delete()
            response = refresh_access_token(settings.ZOHO_APIS_REFRESH_TOKEN, settings.ZOHO_APIS_CLIENT_ID,
                                            settings.ZOHO_APIS_CLIENT_SECRET, settings.ZOHO_APIS_REDIRECT_URI)
            token_expired = True
            access_token = response.get('access_token')
        else:
            access_token = current_access_token.access_token
    return access_token


def get_purchase_orders_list():
    access_token = get_access_token()
    url = "https://www.zohoapis.in/books/v3/purchaseorders"
    params = {
        'organization_id': settings.ZOHO_BOOKS_VEPL_ORGANIZATION_ID,
        'sort_column': 'created_time',
        # 'status': 'billed',
    }
    headers = {"Authorization": "Zoho-oauthtoken " + access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json().get('purchaseorders')


def get_purchase_order_details(purchase_order_id):
    access_token = get_access_token()
    url = "https://www.zohoapis.in/books/v3/purchaseorders/" + purchase_order_id
    params = {
        'organization_id': settings.ZOHO_BOOKS_VEPL_ORGANIZATION_ID,
    }
    headers = {"Authorization": "Zoho-oauthtoken " + access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json().get('purchaseorder')


def get_latest_part_numbers(product_id):
    latest_bom_created_at = BillOfMaterials.objects.filter(product_id=product_id).aggregate(
        latest_created_at=Max('created_at'))['latest_created_at']

    if latest_bom_created_at is None:
        return []

    latest_bom_line_items = BillOfMaterialsLineItem.objects.filter(
        bom__product_id=product_id, bom__created_at=latest_bom_created_at)

    unique_part_numbers = latest_bom_line_items.values_list(
        'part_number', flat=True).distinct()
    return list(unique_part_numbers)


def find_vepl_number(text):
    pattern = re.compile(r'VEPL(\d{8})')

    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    else:
        return None


@shared_task
def update_pricing_for_all_products():
    try:
        logger.info('Update price task started')

        for product in Product.objects.all():
            purchase_orders = get_purchase_orders_list()
            vepl_parts = get_latest_part_numbers(product.id)

            for purchase_order in purchase_orders:
                if len(vepl_parts) != 0:
                    po_details = get_purchase_order_details(
                        purchase_order.get('purchaseorder_id'))
                    po_line_items = po_details.get('line_items')
                    items_to_remove = []
                    for vepl_part in vepl_parts:
                        for po_line_item in po_line_items:
                            logger.debug('vepl_part: %s', vepl_part)
                            logger.debug(
                                'po item: %s', po_line_item.get('sku'))
                            if str(vepl_part).strip() == str(po_line_item.get('sku')).strip():
                                part_pricing, created = PartPricing.objects.update_or_create(part_number=vepl_part, defaults={
                                    'rate': po_line_item.get('rate'),
                                    'part_name': po_line_item.get('name'),
                                    'quantity': po_line_item.get('quantity'),
                                    'total': po_line_item.get('item_total'),
                                    'description': po_line_item.get('description'),
                                    'po_json': po_details,
                                    'product': product,
                                    'project': product.project,
                                })
                                logger.info('SKU match found')
                                items_to_remove.append(vepl_part)

                    for item in items_to_remove:
                        vepl_parts.remove(item)
                else:
                    break

            for vepl_part in vepl_parts:
                part_pricing, created = PartPricing.objects.update_or_create(part_number=vepl_part, defaults={
                    'rate': 0,
                    'part_name': '',
                    'description': '',
                    'quantity': 0,
                    'total': 0,
                    'product': product,
                    'project': product.project,
                })

        return 1

    except Exception as e:
        logger.error(
            'An error occurred in update_pricing_for_all_products: %s', e)
        raise


@shared_task
def create_mfr_part_distributor_data():
    try:
        logger.info('Task started: create_mfr_part_distributor_data')

        # Fetch all ManufacturerPart instances
        manufacturer_parts = ManufacturerPart.objects.all()[:100]
        logger.info(f'Fetched {len(manufacturer_parts)} manufacturer parts')

        # Iterate through each ManufacturerPart
        for manufacturer_part in manufacturer_parts:
            try:
                # Fetch all Distributor instances
                for distributor in Distributor.objects.all():
                    try:
                        if distributor.name.lower() == "digikey":
                            digi_key_distributor_instance = Distributor.objects.get(
                                name="Digikey")
                            if digi_key_distributor_instance.access_id and digi_key_distributor_instance.access_secret:
                                distributor_response = digikey_online_distributor(
                                    digi_key_distributor_instance.access_id,
                                    digi_key_distributor_instance.access_secret,
                                    manufacturer_part.part_number,
                                )
                            else:
                                logger.warning(
                                    "Access ID or Access Secret not available for Digikey")
                        elif distributor.name.lower() == "mouser":
                            mouser_distributor_instance = Distributor.objects.get(
                                name="mouser")
                            if mouser_distributor_instance and mouser_distributor_instance.api_key:
                                distributor_response = mouser_online_distributor(
                                    mouser_distributor_instance.api_key,
                                    manufacturer_part.part_number,
                                )
                                if distributor_response and not distributor_response.get("error"):
                                    pricing = distributor_response.get(
                                        "Pricing", [])
                                    for price in pricing:
                                        if 'Unit Price' in price:
                                            unit_price_str = price['Unit Price']
                                            if unit_price_str.startswith('$'):
                                                unit_price_str = unit_price_str[1:]
                                            try:
                                                unit_price = float(
                                                    unit_price_str)
                                                price['Unit Price'] = unit_price
                                            except ValueError:
                                                logger.error(
                                                    f"Invalid price format: {unit_price_str}")
                                        else:
                                            logger.warning(
                                                "No 'Unit Price' key found in pricing")
                            else:
                                logger.warning(
                                    "Distributor instance or API key not available for Mouser")
                        elif distributor.name.lower() == "element14":
                            element14_distributor_instance = Distributor.objects.get(
                                name="element14")
                            if element14_distributor_instance and element14_distributor_instance.api_key:
                                distributor_response = element14_online_distributor(
                                    element14_distributor_instance.api_key,
                                    manufacturer_part.part_number,
                                )
                            else:
                                logger.warning(
                                    "Distributor instance or API key not available for element14")

                        elif distributor.name.lower() == "samtec" and manufacturer_part.manufacturer.name.lower() == "samtec":
                            samtec_distributor_instance = Distributor.objects.get(
                                name = "samtec"
                            )
                            if samtec_distributor_instance and samtec_distributor_instance.api_key:
                                distributor_response = samtec_own_mfg(
                                    samtec_distributor_instance.api_key,
                                    manufacturer_part.part_number
                                )
                            else:
                                logger.warning(
                                    "Distributor instance or API key not available for samtec")

                        if distributor_response and not distributor_response.get("error"):
                            currency_name = distributor_response.get(
                                "Currency")
                            currency, _ = Currency.objects.get_or_create(
                                name=currency_name)
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
                            pricing = distributor_response.get("Pricing", [])
                            for price in pricing:
                                ManufacturerPartPricing.objects.update_or_create(
                                    manufacturer_part_distributor_detail=mfr_part_distributor_detail,
                                    quantity=price["Quantity"],
                                    defaults={'price': price["Unit Price"]}
                                )
                    except Exception as dist_err:
                        logger.error(
                            f"Error processing distributor {distributor.name}: {dist_err}")
            except Exception as part_err:
                logger.error(
                    f"Error processing manufacturer part {manufacturer_part.part_number}: {part_err}")

        logger.info('Task completed: create_mfr_part_distributor_data')
        return {"message": "Manufacturer part distributor data created successfully"}
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return {"error": "An error occurred"}
