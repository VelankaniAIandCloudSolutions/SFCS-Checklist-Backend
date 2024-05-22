from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from datetime import timedelta, datetime
from .models import *
from .serializers import *
from django.utils import timezone
from store_checklist.models import BillOfMaterials, BillOfMaterialsLineItem, Product, Project
from store_checklist.serializers import BillOfMaterialsSerializer, BillOfMaterialsLineItemSerializer, ProductSerializer, ProjectSerializer , BillOfMaterialsSerializerNew
from django.db.models import Max
import re
from django_celery_results.models import TaskResult
from django.utils import timezone
import pytz
from .tasks import *
from celery.result import AsyncResult
from django.http import Http404

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

@api_view(['GET'])
def get_project_pricing_page(request):
    try:
        projects = Project.objects.all()
        products = Product.objects.all()
        boms = BillOfMaterials.objects.all()
        projects_serializer = ProjectSerializer(projects, many=True)
        products_serializer = ProductSerializer(products, many=True)
        boms_serializer = BillOfMaterialsSerializerNew(boms , many = True)

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
            'boms' : boms_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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