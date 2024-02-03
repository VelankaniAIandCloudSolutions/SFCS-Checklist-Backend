from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from datetime import timedelta, datetime
from .models import *
from django.utils import timezone
from store_checklist.models import BillOfMaterials, BillOfMaterialsLineItem, Product, Project
from store_checklist.serializers import BillOfMaterialsSerializer, BillOfMaterialsLineItemSerializer, ProductSerializer, ProjectSerializer
from django.db.models import Max
import re


def refresh_access_token(refresh_token, client_id, client_secret, redirect_uri):
    url = "https://accounts.zoho.in/oauth/v2/token"
    
    params = {
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url,params=params)
    AccessToken.objects.create(access_token=response.json().get('access_token'), expires_in=response.json().get('expires_in'), expiry_date_time=timezone.now() + timedelta(seconds=response.json().get('expires_in')))
    return response.json()

def get_access_token():

    current_access_token = AccessToken.objects.first()
    token_expired  = False
    if current_access_token is None:
        response = refresh_access_token(settings.ZOHO_APIS_REFRESH_TOKEN, settings.ZOHO_APIS_CLIENT_ID, settings.ZOHO_APIS_CLIENT_SECRET, settings.ZOHO_APIS_REDIRECT_URI)
        token_expired = True
        access_token = response.get('access_token')
    else:
        if current_access_token.expiry_date_time < timezone.now():
            current_access_token.delete()
            response = refresh_access_token(settings.ZOHO_APIS_REFRESH_TOKEN, settings.ZOHO_APIS_CLIENT_ID, settings.ZOHO_APIS_CLIENT_SECRET, settings.ZOHO_APIS_REDIRECT_URI)
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
        'status': 'billed',
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
    latest_bom_created_at = BillOfMaterials.objects.filter(product_id=product_id).aggregate(latest_created_at=Max('created_at'))['latest_created_at']

    if latest_bom_created_at is None:
        return []
    
    latest_bom_line_items = BillOfMaterialsLineItem.objects.filter(bom__product_id=product_id, bom__created_at=latest_bom_created_at)

    unique_part_numbers = latest_bom_line_items.values_list('part_number', flat=True).distinct()
    return list(unique_part_numbers)


def find_vepl_number(text):
    pattern = re.compile(r'VEPL(\d{8})')

    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    else:
        return None


@api_view(['GET'])
def get_product_pricing(request,product_id):
    purchase_orders = get_purchase_orders_list()
    # return Response(purchase_orders)
    # vepl_parts = get_latest_part_numbers(product_id)
    vepl_parts = ['1962','0383']
    vepl_part_latest_prices  = []
    for purchase_order in purchase_orders:
        if len(vepl_parts)!=0:
            po_details  = get_purchase_order_details(purchase_order.get('purchaseorder_id'))
            po_line_items  = po_details.get('line_items')
            for vepl_part in vepl_parts:
                for po_line_item in po_line_items:
                    # if vepl_part == find_vepl_number(po_line_item.get('name')):
                    print(vepl_part)
                    print(po_line_item.get('sku'))
                    if vepl_part == po_line_item.get('sku'):
                        print('sku match')
                        vepl_part_rate = po_line_item.get('rate')
                        vepl_part_quantity = po_line_item.get('quantity')
                        vepl_part_total =  po_line_item.get('item_total')
                        vepl_part_name = po_line_item.get('name')
                        vepl_part_description = po_line_item.get('description')
                        vepl_part_latest_prices.append({
                            'part_number': vepl_part,
                            'name': vepl_part_name,
                            'description': vepl_part_description,
                            'rate': vepl_part_rate,
                            'quantity': vepl_part_quantity,
                            'total': vepl_part_total,
                            'po': po_details
                        })
                        if vepl_part in vepl_parts:
                            vepl_parts.remove(vepl_part)
        else:   
            break
        
    vepl_part_latest_prices.extend([{
        'part_number': vepl_part,
        'name': '',
        'description': '',
        'rate': '',
        'quantity': '',
        'total': ''
    } for vepl_part in vepl_parts])
    
    data = {
        'part_prices': vepl_part_latest_prices,
        'latest_parts': vepl_parts
    }
    return Response(data,status=status.HTTP_200_OK)

@api_view(['GET'])
def get_project_pricing_page(request):
    projects  = Project.objects.all()
    products = Product.objects.all()
    projects_serializer  = ProjectSerializer(projects, many=True)
    products_serializer = ProductSerializer(products, many=True)
    data = {
        'projects': projects_serializer.data,
        'products': products_serializer.data
    }
    return Response(data,status=status.HTTP_200_OK)